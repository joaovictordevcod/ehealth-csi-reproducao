"""
analyze.py — Roda a análise a partir de um features.npz já calculado.

Evita recalcular o DTW, que é a etapa cara do pipeline. Use quando quiser
reavaliar classificadores, seleção de atributos ou composição do holdout sem
reprocessar o dataset.

Uso:
    python3 analyze.py [features.npz]
"""
import sys
import numpy as np

from run_experiment import (run_split, run_holdout, run_feature_selection,
                            compare, save_run)


def main(path="features.npz"):
    d = np.load(path)
    X, y, g = d["X"], d["y"], d["groups"]

    bom = np.isfinite(X).all(axis=1)
    n_desc = int((~bom).sum())
    if n_desc:
        print(f"descartadas {n_desc} de {len(X)} instâncias com valor não-finito "
              f"({n_desc / len(X) * 100:.1f}%)")
    X, y, g = X[bom], y[bom], g[bom]
    print(f"dataset: {X.shape} | classe 1={int(y.sum())} | "
          f"classe 0={int((y == 0).sum())}")

    t3 = run_split(X, y, label="Tabela 3 — balanceado, 70/30")
    compare(t3, "tabela3_balanceado")

    fs = run_feature_selection(X, y)

    ids = sorted(set(g.tolist()))
    t4 = run_holdout(X, y, g, ids[-18:],
                     label="Tabela 4 — 18 participantes não vistos")
    compare(t4, "tabela4_holdout")

    save_run("registro_execucao.json", tabela3=t3, tabela4=t4,
             selecao_features=fs, instancias_descartadas=n_desc)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "features.npz")
