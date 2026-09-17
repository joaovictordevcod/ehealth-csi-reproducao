"""
run_experiment.py — Classificação e tabelas de resultado

Reproduz a Seção VII de Galdino et al. (IEEE Access 2023), com o método
detalhado em Soto et al. (LATINCOM 2022).

Alvos:
    Tabela 3 (balanceado)      SVM 99.90 | RF 99.90 | J48 94.90 | NB 93.43
    Tabela 4 (18 não vistos)   RF 91.18 | J48 78.92 | NB 83.33 | SVM 76.47
    LATINCOM Fig. 3            5 features -> RF ~99.98
"""
import json
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import (accuracy_score, precision_score,
                             recall_score, f1_score, confusion_matrix)

from csi_pipeline import PARAMS


def make_classifiers(seed=None):
    """Classificadores conforme descritos nos artigos.

    J48 é a implementação Weka do C4.5; em Python usamos DecisionTreeClassifier
    com critério de entropia e profundidade 3, conforme o texto. Não é
    idêntico ao J48 — essa substituição deve constar no relatório.
    """
    seed = PARAMS["random_state"] if seed is None else seed
    return {
        # StandardScaler: o SMO do Weka, usado pelos autores, padroniza os
        # dados de treino por padrão. Ver DECISOES.md.
        "SVM": make_pipeline(StandardScaler(),
                             SVC(kernel="linear", random_state=seed)),
        "J48": DecisionTreeClassifier(criterion="entropy", max_depth=3,
                                      random_state=seed),
        "NB":  make_pipeline(StandardScaler(), GaussianNB()),
        "RF":  RandomForestClassifier(n_estimators=100, random_state=seed),
    }


def evaluate(y_true, y_pred):
    return {
        "accuracy":  accuracy_score(y_true, y_pred) * 100,
        "precision": precision_score(y_true, y_pred, zero_division=0) * 100,
        "recall":    recall_score(y_true, y_pred, zero_division=0) * 100,
        "f1":        f1_score(y_true, y_pred, zero_division=0) * 100,
    }


def run_split(X, y, test_size=None, seed=None, label=""):
    """Treino/teste com divisão aleatória estratificada."""
    test_size = PARAMS["test_size"] if test_size is None else test_size
    seed = PARAMS["random_state"] if seed is None else seed

    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y)

    rows = []
    for name, clf in make_classifiers(seed).items():
        clf.fit(Xtr, ytr)
        m = evaluate(yte, clf.predict(Xte))
        m["classificador"] = name
        rows.append(m)

    df = pd.DataFrame(rows).set_index("classificador")
    if label:
        print(f"\n=== {label} ===")
        print(f"treino: {len(ytr)} | teste: {len(yte)} | "
              f"classe 1: {int(y.sum())} | classe 0: {int((y == 0).sum())}")
        print(df.round(2).to_string())
    return df


def run_holdout(X, y, groups, holdout_ids, seed=None, label=""):
    """Treina nos participantes de dentro, testa nos que ficaram de fora.

    É o experimento da Tabela 4 — o único que mede generalização real.
    """
    seed = PARAMS["random_state"] if seed is None else seed
    groups = np.asarray(groups)
    m_out = np.isin(groups, list(holdout_ids))

    Xtr, ytr = X[~m_out], y[~m_out]
    Xte, yte = X[m_out], y[m_out]

    rows = []
    for name, clf in make_classifiers(seed).items():
        clf.fit(Xtr, ytr)
        m = evaluate(yte, clf.predict(Xte))
        m["classificador"] = name
        rows.append(m)

    df = pd.DataFrame(rows).set_index("classificador")
    if label:
        print(f"\n=== {label} ===")
        print(f"treino: {len(ytr)} instâncias | "
              f"teste: {len(yte)} instâncias de {len(set(holdout_ids))} participantes")
        print(df.round(2).to_string())
    return df


def run_feature_selection(X, y, ks=(5, 10, 20, 50, 100, 234), seed=None):
    """Curva de desempenho x número de features (Figura 3 do LATINCOM)."""
    seed = PARAMS["random_state"] if seed is None else seed
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=PARAMS["test_size"], random_state=seed, stratify=y)

    rows = []
    for k in ks:
        if k > X.shape[1]:
            continue
        sel = SelectKBest(f_classif, k=k).fit(Xtr, ytr)
        Xtr_k, Xte_k = sel.transform(Xtr), sel.transform(Xte)
        for name, clf in make_classifiers(seed).items():
            clf.fit(Xtr_k, ytr)
            rows.append({"k": k, "classificador": name,
                         "accuracy": accuracy_score(yte, clf.predict(Xte_k)) * 100})

    df = pd.DataFrame(rows).pivot(index="k", columns="classificador",
                                  values="accuracy")
    print("\n=== Seleção de features (acurácia %) ===")
    print(df.round(2).to_string())
    return df


ALVOS = {
    "tabela3_balanceado": {"SVM": 99.90, "J48": 94.90, "NB": 93.43, "RF": 99.90},
    "tabela4_holdout":    {"SVM": 76.47, "J48": 78.92, "NB": 83.33, "RF": 91.18},
}


def compare(df, alvo_nome):
    """Compara o resultado obtido com os números publicados."""
    alvo = ALVOS[alvo_nome]
    out = pd.DataFrame({
        "obtido": df["accuracy"].round(2),
        "publicado": pd.Series(alvo),
    })
    out["diferença"] = (out["obtido"] - out["publicado"]).round(2)
    print(f"\n=== Comparação com {alvo_nome} ===")
    print(out.to_string())
    return out


def save_run(path, **artefatos):
    """Grava parâmetros e resultados — o registro de decisões do relatório."""
    payload = {"parametros": PARAMS}
    for k, v in artefatos.items():
        payload[k] = v.to_dict() if hasattr(v, "to_dict") else v
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, default=str)
    print(f"\nregistro salvo em {path}")


if __name__ == "__main__":
    import sys
    from csi_pipeline import build_dataset, build_subcarrier_mask

    root = sys.argv[1] if len(sys.argv) > 1 else "eHealth"
    mask = build_subcarrier_mask()
    print(f"máscara: {mask.sum()} subportadoras de dados")

    X, y, meta = build_dataset(root, mask=mask)
    groups = [m["participant"] for m in meta]
    print(f"\ndataset: X={X.shape} | classe 1={int(y.sum())} | classe 0={int((y==0).sum())}")

    np.savez_compressed("features.npz", X=X, y=y, groups=groups)
    print("features salvas em features.npz")

    t3 = run_split(X, y, label="Tabela 3 — balanceado, 70/30")
    compare(t3, "tabela3_balanceado")

    fs = run_feature_selection(X, y)

    ids = sorted(set(groups))
    holdout = ids[-18:]
    t4 = run_holdout(X, y, groups, holdout, label="Tabela 4 — 18 participantes não vistos")
    compare(t4, "tabela4_holdout")

    save_run("registro_execucao.json", tabela3=t3, tabela4=t4, selecao_features=fs)
