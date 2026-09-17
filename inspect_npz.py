"""
Inspetor de arquivos .npz do eHealth CSI (formato pré-processado, chipset Broadcom/Nexmon).

Uso:
    python3 inspect_npz.py caminho/para/arquivo.npz [pasta_saida]

Gera 4 figuras de diagnóstico e imprime um resumo textual da arquitetura do arquivo.
Não depende de nada além de numpy e matplotlib -- roda local, sem precisar do dataset inteiro.
"""
import sys
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def inspect(path: str, outdir: str = "."):
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]

    d = np.load(path, allow_pickle=True)
    csi = d["csi"]          # (n_pacotes, n_subportadoras) complex
    ts = d["ts"]             # (n_pacotes,) float64, segundos desde epoch
    meta = d["metadata"]     # array de dicts: meta[0] = resumo do arquivo, meta[1:] = 1 dict por pacote

    n_pkts, n_sub = csi.shape
    duration = ts[-1] - ts[0]
    dt = np.diff(ts)
    amp = np.abs(csi)

    file_summary = meta[0]
    pkt0 = meta[1]

    print("=" * 60)
    print(f"ARQUIVO: {os.path.basename(path)}")
    print("=" * 60)
    print(f"Tamanho em disco:      {os.path.getsize(path)/1e6:.2f} MB")
    print()
    print("--- Arrays no .npz ---")
    print(f"csi       shape={csi.shape}  dtype={csi.dtype}")
    print(f"ts        shape={ts.shape}   dtype={ts.dtype}")
    print(f"metadata  shape={meta.shape} dtype={meta.dtype}  (array de dicts Python)")
    print()
    print("--- metadata[0]: resumo do arquivo ---")
    print(file_summary)
    print()
    print("--- metadata[1]: primeiro pacote (mesma estrutura para todos) ---")
    for k, v in pkt0.items():
        print(f"  {k}: {v}")
    print()
    print("--- Temporal ---")
    print(f"n_pacotes:             {n_pkts}")
    print(f"duracao total (s):     {duration:.2f}")
    print(f"taxa media (pkt/s):    {n_pkts/duration:.2f}")
    print(f"intervalo entre pacotes (ms): media={dt.mean()*1000:.2f}  "
          f"std={dt.std()*1000:.2f}  min={dt.min()*1000:.2f}  max={dt.max()*1000:.2f}")
    print()
    print("--- CSI / amplitude ---")
    print(f"NaN:  {np.isnan(csi.real).sum() + np.isnan(csi.imag).sum()}")
    print(f"Inf:  {np.isinf(amp).sum()}")
    mean_amp = amp.mean(axis=0)
    med = np.median(mean_amp)
    outliers = np.where(mean_amp > 5 * med)[0]
    print(f"mediana da amplitude media entre subportadoras: {med:.2f}")
    print(f"subportadoras com amplitude media > 5x a mediana: {len(outliers)}")
    if len(outliers):
        print(f"  indices: {outliers.min()}..{outliers.max()} "
              f"({'contiguo' if (outliers.max()-outliers.min()+1)==len(outliers) else 'NAO contiguo'})")
    print()

    # ---------- Figura 1: heatmap tempo x subportadora ----------
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(np.log1p(amp), aspect="auto", cmap="viridis",
                    extent=[0, n_sub, duration, 0])
    ax.set_xlabel("Índice da subportadora")
    ax.set_ylabel("Tempo (s)")
    ax.set_title(f"Amplitude do CSI ao longo do tempo — {base}\n(escala log1p, eixo do tempo invertido)")
    fig.colorbar(im, ax=ax, label="log(1 + amplitude)")
    fig.tight_layout()
    p1 = os.path.join(outdir, f"{base}_heatmap.png")
    fig.savefig(p1, dpi=130)
    plt.close(fig)

    # ---------- Figura 2: perfil medio por subportadora ----------
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    axes[0].plot(mean_amp, lw=0.9, color="#1D8FB8")
    axes[0].set_ylabel("Amplitude média (linear)")
    axes[0].set_title(f"Perfil médio de amplitude por subportadora — {base}")
    axes[0].axhline(5*med, color="#E8590C", ls="--", lw=0.8, label="5x mediana")
    axes[0].legend(fontsize=8)
    axes[1].plot(mean_amp, lw=0.9, color="#1D8FB8")
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Amplitude média (log)")
    axes[1].set_xlabel("Índice da subportadora (0-255)")
    fig.tight_layout()
    p2 = os.path.join(outdir, f"{base}_perfil_subportadoras.png")
    fig.savefig(p2, dpi=130)
    plt.close(fig)

    # ---------- Figura 3: series temporais de subportadoras "limpas" ----------
    clean_idx = [i for i in [10, 50, 80, 200, 230] if i < n_sub]
    fig, ax = plt.subplots(figsize=(11, 4.5))
    t = ts - ts[0]
    for i in clean_idx:
        ax.plot(t, amp[:, i], lw=0.8, label=f"subportadora {i}")
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title(f"Série temporal de amplitude — algumas subportadoras — {base}")
    ax.legend(fontsize=8, ncol=5)
    fig.tight_layout()
    p3 = os.path.join(outdir, f"{base}_series_temporais.png")
    fig.savefig(p3, dpi=130)
    plt.close(fig)

    # ---------- Figura 4: histograma do intervalo entre pacotes ----------
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(dt * 1000, bins=60, color="#F08C00", edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Intervalo entre pacotes consecutivos (ms)")
    ax.set_ylabel("Contagem")
    ax.set_title(f"Distribuição do intervalo entre pacotes — {base}\n"
                 f"média={dt.mean()*1000:.1f} ms, desvio-padrão={dt.std()*1000:.1f} ms")
    fig.tight_layout()
    p4 = os.path.join(outdir, f"{base}_intervalo_pacotes.png")
    fig.savefig(p4, dpi=130)
    plt.close(fig)

    print("--- Figuras geradas ---")
    for p in [p1, p2, p3, p4]:
        print(" ", p)

    return dict(n_pkts=n_pkts, n_sub=n_sub, duration=duration, dt=dt,
                mean_amp=mean_amp, outliers=outliers, figs=[p1, p2, p3, p4])


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    if path is None:
        print("Uso: python3 inspect_npz.py arquivo.npz [pasta_saida]")
        sys.exit(1)
    inspect(path, outdir)
