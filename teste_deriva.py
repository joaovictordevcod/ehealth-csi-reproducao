"""
teste_deriva.py — O ambiente mudou ao longo da coleta?

Todas as features são distâncias DTW contra UMA referência de sala vazia, a do
participante 001. Os identificadores são sequenciais por ordem de coleta, que se
estendeu por meses.

Se a sala mudou nesse período — móveis, equipamentos, posição da antena — a
distância até a referência cresce com o número do participante, mesmo para
gravações de sala vazia. Isso faz salas vazias tardias parecerem ocupadas, e
explicaria por que os primeiros participantes são classificados melhor que os
últimos.

Este script mede essa correlação. Usa features já calculadas.

Uso:
    python3 teste_deriva.py [features.npz]
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats


def main(path="features_seg29.npz"):
    d = np.load(path)
    X, y, g = d["X"], d["y"], d["groups"]
    bom = np.isfinite(X).all(axis=1)
    X, y, g = X[bom], y[bom], g[bom]

    # distância média de cada instância até a referência
    dist = X.mean(axis=1)

    print(f"{path}: {len(X)} instâncias, {len(set(g.tolist()))} participantes\n")

    linhas = []
    for rotulo, nome in [(0, "sala vazia"), (1, "sala ocupada")]:
        m = y == rotulo
        gp = g[m]
        dp = dist[m]

        # média por participante
        ids = np.array(sorted(set(gp.tolist())))
        medias = np.array([dp[gp == i].mean() for i in ids])

        rho, p = stats.spearmanr(ids, medias)
        r, p_r = stats.pearsonr(ids, medias)

        linhas.append({
            "classe": nome,
            "n_participantes": len(ids),
            "spearman_rho": round(rho, 3),
            "spearman_p": f"{p:.2e}",
            "pearson_r": round(r, 3),
            "1o_terco": round(medias[:len(ids) // 3].mean(), 1),
            "2o_terco": round(medias[len(ids) // 3:2 * len(ids) // 3].mean(), 1),
            "3o_terco": round(medias[2 * len(ids) // 3:].mean(), 1),
        })

    df = pd.DataFrame(linhas).set_index("classe")
    print("Distância média até a referência, por classe\n")
    print(df.to_string())

    v = df.loc["sala vazia"]
    razao = v["3o_terco"] / v["1o_terco"]
    print(f"\nSala vazia — último terço / primeiro terço: {razao:.2f}x")

    print("\nLeitura:")
    print("  rho próximo de 0    -> sem deriva; a diferença tem outra causa")
    print("  rho alto e positivo -> deriva confirmada; a referência única é")
    print("                         inadequada para coletas longas")

    # separabilidade das classes por faixa de coleta
    print("\n\nSeparabilidade entre as classes, por faixa de coleta")
    print("(distância média: ocupada menos vazia — quanto maior, mais fácil)\n")
    ids_all = np.array(sorted(set(g.tolist())))
    n = len(ids_all)
    for nome_faixa, sel in [("primeiro terço", ids_all[:n // 3]),
                            ("segundo terço", ids_all[n // 3:2 * n // 3]),
                            ("último terço", ids_all[2 * n // 3:])]:
        m = np.isin(g, sel)
        d1 = dist[m & (y == 1)].mean()
        d0 = dist[m & (y == 0)].mean()
        print(f"  {nome_faixa:16s}: ocupada {d1:7.1f} | vazia {d0:7.1f} | "
              f"diferença {d1 - d0:7.1f}")

    df.to_csv("teste_deriva.csv")
    print("\nresultados em teste_deriva.csv")
    return df


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "features_seg29.npz")
