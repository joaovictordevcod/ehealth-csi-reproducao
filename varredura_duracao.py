"""
varredura_duracao.py — Efeito da duração do segmento no desempenho

Monta o dataset para vários comprimentos de segmento e avalia cada um, nos dois
protocolos: divisão aleatória 70/30 (Tabela 3) e participantes não vistos
(Tabela 4).

Motivação: a primeira execução com comprimento uniforme usou segmentos de 29
amostras (~3,3 s) e o desempenho ficou muito abaixo do publicado. A hipótese é
que a duração do segmento seja o fator determinante. Esta varredura testa isso.

ATENÇÃO — sobreposição. Para obter 1700 instâncias de sala vazia com segmentos
longos, as janelas precisam se sobrepor, já que existe só uma gravação de
posição 0 por participante. Janelas sobrepostas do mesmo participante são
quase duplicatas: na divisão aleatória elas caem em treino e teste ao mesmo
tempo, inflando o resultado. O protocolo por participante não sofre disso.
Por isso a comparação entre as duas colunas é o resultado que interessa.

Uso:
    python3 varredura_duracao.py /caminho/Data_DS2_raspberry_npz
"""
import sys
import json
import numpy as np
import pandas as pd

from csi_pipeline import build_dataset, build_subcarrier_mask, PARAMS
from run_experiment import run_split, run_holdout

TAXA_HZ = 34.9   # taxa medida no DS2


def duracao_s(seg_len):
    return seg_len * PARAMS["subsample"] / TAXA_HZ


def varrer(root, comprimentos=(29, 60, 125, 250, 400), n_holdout=18):
    mask = build_subcarrier_mask()
    linhas = []

    for seg_len in comprimentos:
        print(f"\n{'=' * 64}")
        print(f"seg_len = {seg_len} amostras (~{duracao_s(seg_len):.1f} s)")
        print("=" * 64)

        X, y, meta = build_dataset(root, mask=mask, seg_len=seg_len,
                                   verbose=True)
        g = np.array([m["participant"] for m in meta])

        bom = np.isfinite(X).all(axis=1)
        X, y, g = X[bom], y[bom], g[bom]
        print(f"instâncias: {len(X)} | classe 1={int(y.sum())} | "
              f"classe 0={int((y == 0).sum())} | descartadas={int((~bom).sum())}")

        t3 = run_split(X, y, label=f"aleatório 70/30 — {seg_len} amostras")
        ids = sorted(set(g.tolist()))
        t4 = run_holdout(X, y, g, ids[-n_holdout:],
                         label=f"participantes não vistos — {seg_len} amostras")

        for clf in t3.index:
            linhas.append({
                "seg_len": seg_len,
                "duracao_s": round(duracao_s(seg_len), 1),
                "classificador": clf,
                "acc_aleatorio": round(t3.loc[clf, "accuracy"], 2),
                "acc_holdout": round(t4.loc[clf, "accuracy"], 2),
                "queda": round(t3.loc[clf, "accuracy"] - t4.loc[clf, "accuracy"], 2),
            })

        np.savez_compressed(f"features_seg{seg_len}.npz", X=X, y=y, groups=g)

    df = pd.DataFrame(linhas)

    print(f"\n\n{'=' * 64}")
    print("RESUMO — acurácia (%) por duração do segmento")
    print("=" * 64)
    for col, titulo in [("acc_aleatorio", "Divisão aleatória 70/30 (Tabela 3)"),
                        ("acc_holdout", "Participantes não vistos (Tabela 4)"),
                        ("queda", "Queda entre os dois protocolos")]:
        print(f"\n{titulo}")
        print(df.pivot(index="duracao_s", columns="classificador",
                       values=col).to_string())

    df.to_csv("varredura_duracao.csv", index=False)
    with open("varredura_duracao.json", "w") as fh:
        json.dump({"parametros": PARAMS, "resultados": linhas}, fh,
                  indent=2, ensure_ascii=False)
    print("\nresultados em varredura_duracao.csv e varredura_duracao.json")
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    varrer(sys.argv[1])
