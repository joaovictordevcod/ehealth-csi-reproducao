"""
teste_holdout.py — A escolha dos 18 participantes afeta o resultado?

O protocolo da Tabela 4 separa 18 participantes do treino. Os artigos não dizem
quais. Nossa implementação usa os 18 maiores identificadores — e como os IDs são
sequenciais por ordem de coleta, isso equivale a testar nos participantes
coletados por último, os mais distantes no tempo da referência de sala vazia
(participante 001).

Se houver deriva do ambiente ao longo dos meses de coleta, essa escolha é o pior
caso possível. Este script compara:

    - últimos 18 identificadores   (nossa escolha atual)
    - primeiros 18                 (mais próximos da referência)
    - 18 sorteados                 (várias repetições, para ter distribuição)

Usa features já calculadas — não recalcula DTW.

Uso:
    python3 teste_holdout.py [features.npz] [n_repeticoes]
"""
import sys
import numpy as np
import pandas as pd

from run_experiment import make_classifiers, evaluate


def avaliar(X, y, g, holdout_ids, seed=42):
    fora = np.isin(g, list(holdout_ids))
    Xtr, ytr = X[~fora], y[~fora]
    Xte, yte = X[fora], y[fora]
    if len(set(ytr)) < 2 or len(set(yte)) < 2:
        return None
    out = {}
    for nome, clf in make_classifiers(seed).items():
        clf.fit(Xtr, ytr)
        out[nome] = evaluate(yte, clf.predict(Xte))["accuracy"]
    return out


def main(path="features.npz", n_rep=20):
    d = np.load(path)
    X, y, g = d["X"], d["y"], d["groups"]
    bom = np.isfinite(X).all(axis=1)
    X, y, g = X[bom], y[bom], g[bom]

    ids = np.array(sorted(set(g.tolist())))
    print(f"{path}: {len(X)} instâncias, {len(ids)} participantes "
          f"(ID {ids.min()} a {ids.max()})\n")

    cenarios = {
        "últimos 18": ids[-18:],
        "primeiros 18": ids[:18],
    }

    linhas = []
    for nome, sel in cenarios.items():
        r = avaliar(X, y, g, sel)
        if r:
            linhas.append({"cenário": nome, **{k: round(v, 2) for k, v in r.items()}})

    # sorteios
    rng = np.random.default_rng(0)
    sorteios = []
    for i in range(n_rep):
        sel = rng.choice(ids, size=18, replace=False)
        r = avaliar(X, y, g, sel, seed=42)
        if r:
            sorteios.append(r)
        print(f"  sorteio {i + 1}/{n_rep}", end="\r")
    print(" " * 30, end="\r")

    df_s = pd.DataFrame(sorteios)
    linhas.append({"cenário": f"sorteado — média ({len(df_s)}x)",
                   **df_s.mean().round(2).to_dict()})
    linhas.append({"cenário": "sorteado — desvio-padrão",
                   **df_s.std().round(2).to_dict()})
    linhas.append({"cenário": "sorteado — mínimo",
                   **df_s.min().round(2).to_dict()})
    linhas.append({"cenário": "sorteado — máximo",
                   **df_s.max().round(2).to_dict()})

    df = pd.DataFrame(linhas).set_index("cenário")
    print("Acurácia (%) no teste com 18 participantes não vistos\n")
    print(df.to_string())

    print("\nPublicado (Tabela 4):  SVM 76,47 | J48 78,92 | NB 83,33 | RF 91,18")

    df.to_csv("teste_holdout.csv")
    print("\nresultados em teste_holdout.csv")
    return df


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "features.npz"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    main(p, n)
