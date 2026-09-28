"""
csi_pipeline.py — Reprodução da detecção de presença por Wi-Fi CSI
                  (Soto et al., LATINCOM 2022 / Galdino et al., IEEE Access 2023)

Pipeline:
    .npz  ->  amplitude  ->  Hampel  ->  média móvel
          ->  DTW contra referência de sala vazia  ->  234 features
          ->  classificadores

Todas as decisões não documentadas nos artigos estão reunidas em PARAMS,
para serem registradas no relatório de reprodução.
"""
import re
import numpy as np
from pathlib import Path
from dtaidistance import dtw

# ─────────────────────────────────────────────────────────────────────────
# PARÂMETROS — decisões nossas, não documentadas nos artigos.
# Cada um destes precisa aparecer no relatório.
# ─────────────────────────────────────────────────────────────────────────
PARAMS = {
    # Hampel: nem a janela nem o limiar são informados nos artigos
    "hampel_window": 7,
    "hampel_sigma": 3.0,

    # Média móvel: tamanho não informado
    "movavg_window": 5,

    # Subamostragem: DS2 foi coletado a ~33 Hz (2000 pacotes/min), mas os
    # artigos descrevem ~8-9 Hz (DS1, 500 pacotes/min). Subamostrar por 4
    # aproxima a taxa do protocolo descrito E reduz o custo do DTW em ~10x.
    "subsample": 4,

    # DTW: variante e restrição de banda não informadas.
    # window=None -> DTW irrestrito (mais fiel ao texto, mais lento)
    "dtw_window": 50,

    # Subportadoras: 80 MHz -> 256 no total, 234 úteis segundo os artigos.
    # A máscara é definida empiricamente (ver build_subcarrier_mask).
    "n_subcarriers_target": 234,

    # Divisão treino/teste
    "test_size": 0.30,
    "random_state": 42,
}

FNAME_RE = re.compile(
    r"(?P<position>\d+)_(?P<date>\d{4}_\d{2}_\d{2})_-_(?P<time>\d{2}_\d{2}_\d{2})"
    r"_bw_(?P<bw>\d+)_ch_(?P<ch>\d+)\.npz$"
)


# ─────────────────────────────────────────────────────────────────────────
# Leitura e pré-processamento
# ─────────────────────────────────────────────────────────────────────────
def load_amplitude(path, subsample=None):
    """Lê um .npz e devolve a amplitude do CSI: (n_amostras, n_subportadoras)."""
    sub = PARAMS["subsample"] if subsample is None else subsample
    d = np.load(path, allow_pickle=True)
    amp = np.abs(d["csi"]).astype(np.float64)
    if sub and sub > 1:
        amp = amp[::sub]
    return amp


def hampel(x, window=None, n_sigma=None):
    """Filtro de Hampel vetorizado, ao longo do eixo do tempo.

    Substitui pontos que se afastam mais de n_sigma MADs da mediana local.
    Implementação vetorizada — a versão com laço em Python é ~100x mais lenta.
    """
    k = PARAMS["hampel_window"] if window is None else window
    ns = PARAMS["hampel_sigma"] if n_sigma is None else n_sigma
    half = k // 2
    n = x.shape[0]
    if n <= k:
        return x.copy()

    # janelas deslizantes: (n - k + 1, k, n_sub)
    win = np.lib.stride_tricks.sliding_window_view(x, k, axis=0)  # (n-k+1, n_sub, k)
    med = np.median(win, axis=-1)                                  # (n-k+1, n_sub)
    mad = np.median(np.abs(win - med[..., None]), axis=-1)
    thr = ns * 1.4826 * mad

    out = x.copy()
    core = out[half:n - half]
    bad = np.abs(core - med) > thr
    core[bad] = med[bad]
    out[half:n - half] = core
    return out


def moving_average(x, window=None):
    """Média móvel causal-centrada ao longo do tempo, com bordas preservadas."""
    w = PARAMS["movavg_window"] if window is None else window
    if w <= 1:
        return x.copy()
    kernel = np.ones(w) / w
    out = np.empty_like(x)
    for j in range(x.shape[1]):
        out[:, j] = np.convolve(x[:, j], kernel, mode="same")
    return out


def preprocess(amp):
    """amplitude -> Hampel -> média móvel."""
    return moving_average(hampel(amp))


# ─────────────────────────────────────────────────────────────────────────
# Máscara de subportadoras
# ─────────────────────────────────────────────────────────────────────────
def build_subcarrier_mask(n_fft=256):
    """Máscara das 234 subportadoras de dados, conforme IEEE 802.11ac @ 80 MHz.

    Estrutura do padrão para FFT de 256 pontos (índices lógicos -128..+127,
    índice do array = lógico + 128):
        guarda à esquerda : -128..-123   (6)
        guarda à direita  : +123..+127   (5)
        DC                : -1, 0, +1    (3)
        pilotos           : ±11, ±39, ±75, ±103   (8)
                                              total descartado = 22
        256 - 22 = 234 subportadoras de dados  <- número usado nos artigos

    Verificado empiricamente: os índices de DC (127, 128, 129) aparecem com
    amplitude ~50x acima da mediana, confirmando a estrutura.
    """
    if n_fft != 256:
        raise NotImplementedError("máscara definida apenas para FFT de 256 (80 MHz)")
    c = n_fft // 2
    descartar = set(range(0, 6)) | set(range(251, 256)) | {c - 1, c, c + 1}
    descartar |= {c + o for o in (-103, -75, -39, -11, 11, 39, 75, 103)}
    mask = np.ones(n_fft, dtype=bool)
    mask[sorted(descartar)] = False
    assert mask.sum() == 234, f"esperado 234, obtido {mask.sum()}"
    return mask


# ─────────────────────────────────────────────────────────────────────────
# Features por DTW
# ─────────────────────────────────────────────────────────────────────────
def dtw_features(amp_proc, ref_proc, mask=None, window=None):
    """Distância DTW subportadora a subportadora contra a referência.

    Devolve um vetor de tamanho = número de subportadoras na máscara.
    """
    w = PARAMS["dtw_window"] if window is None else window
    if mask is None:
        mask = np.ones(amp_proc.shape[1], dtype=bool)
    idx = np.where(mask)[0]

    # A banda precisa ser maior que a diferença de comprimento entre as séries,
    # senão o caminho não alcança o fim e o DTW devolve infinito.
    if w:
        w = max(w, abs(amp_proc.shape[0] - ref_proc.shape[0]) + 1)

    feats = np.empty(len(idx))
    for i, j in enumerate(idx):
        a = np.ascontiguousarray(amp_proc[:, j])
        b = np.ascontiguousarray(ref_proc[:, j])
        v = dtw.distance_fast(a, b, window=w)
        if not np.isfinite(v):
            # Séries degeneradas (subportadoras nulas, constantes) quebram a
            # poda da implementação em C. Recalcula em Python puro, que é
            # robusto a esses casos. Ver DIARIO.md, "Problemas encontrados".
            v = dtw.distance(a, b, window=w)
        feats[i] = v
    return feats


def parse_name(path):
    m = FNAME_RE.search(Path(path).name)
    if not m:
        return None
    return {"position": int(m.group("position")),
            "date": m.group("date"), "time": m.group("time")}


def participant_of(path, root):
    for part in reversed(Path(path).relative_to(root).parts[:-1]):
        if part.isdigit():
            return int(part)
    return None


# ─────────────────────────────────────────────────────────────────────────
# Construção do dataset
# ─────────────────────────────────────────────────────────────────────────
def _segmento_central(serie, seg_len):
    """Trecho central de `seg_len` amostras.

    Usa o centro e não o início para evitar o transiente do começo da gravação,
    em que o participante ainda está se acomodando na posição.
    """
    ini = max(0, (len(serie) - seg_len) // 2)
    return serie[ini:ini + seg_len]


def build_dataset(root, participants=None, ref_file=None, mask=None,
                  n_empty_segments=17, seg_len=None, verbose=True):
    """Percorre o dataset e monta X (features) e y (rótulos).

    Classe 1 = sala ocupada (posições 1..17), um segmento por gravação
    Classe 0 = sala vazia (posição 0), `n_empty_segments` segmentos por gravação

    IMPORTANTE — comprimento uniforme
    ---------------------------------
    Todas as instâncias, das duas classes, usam segmentos do MESMO comprimento.

    A distância DTW cresce com o comprimento das séries comparadas. Uma versão
    anterior deste código usava a gravação inteira (~500 amostras) para a classe
    1 e segmentos (~29 amostras) para a classe 0. O resultado foi uma diferença
    sistemática de escala entre as classes — mediana de 209 contra 71 — que os
    classificadores exploravam como atalho, produzindo desempenho artificialmente
    alto inclusive em participantes nunca vistos. Ver DIARIO.md.

    n_empty_segments: quantos trechos extrair de cada gravação de sala vazia.
        Os artigos relatam 1700 instâncias vazias a partir de ~100 gravações,
        o que implica 17 segmentos por gravação. Com 17 posições ocupadas por
        participante, a proporção resulta balanceada. Essa inferência precisa
        constar no relatório.
    """
    root = Path(root)
    files = sorted(root.rglob("*.npz"))

    por_participante = {}
    for f in files:
        p = participant_of(f, root)
        info = parse_name(f)
        if p is None or info is None:
            continue
        if participants is not None and p not in participants:
            continue
        por_participante.setdefault(p, {})[info["position"]] = f

    X, y, meta = [], [], []

    # referência global de sala vazia
    if ref_file is None:
        for p, posmap in sorted(por_participante.items()):
            if 0 in posmap:
                ref_file = posmap[0]
                break
    if ref_file is None:
        raise RuntimeError("nenhuma gravação de sala vazia (posição 0) encontrada")
    if verbose:
        print(f"referência de sala vazia: {Path(ref_file).name}")

    ref_proc = preprocess(load_amplitude(ref_file))
    n_total = len(ref_proc)

    # Comprimento comum a todas as instâncias das duas classes.
    if seg_len is None:
        seg_len = n_total // n_empty_segments      # sem sobreposição
    seg_len = min(int(seg_len), n_total)
    if seg_len < 10:
        raise RuntimeError(f"segmento de {seg_len} amostras é curto demais")

    # Janelas da sala vazia: uniformemente espaçadas ao longo da gravação.
    # Quando seg_len > n_total / n_empty_segments elas se sobrepõem — o que é
    # necessário para obter 1700 instâncias com séries longas. A sobreposição
    # é registrada em `overlap` e precisa constar no relatório.
    max_ini = n_total - seg_len
    inicios = (np.linspace(0, max_ini, n_empty_segments).astype(int)
               if max_ini > 0 else np.zeros(n_empty_segments, dtype=int))
    passo = int(np.median(np.diff(inicios))) if n_empty_segments > 1 else seg_len
    overlap = max(0.0, 1 - passo / seg_len) if seg_len else 0.0

    ref_seg = _segmento_central(ref_proc, seg_len)
    if verbose:
        dur = seg_len * PARAMS["subsample"] / 34.9   # taxa medida do DS2
        print(f"segmento: {seg_len} amostras (~{dur:.1f} s) "
              f"de {n_total} | sobreposição entre janelas vazias: "
              f"{overlap * 100:.0f}%")

    for n, (p, posmap) in enumerate(sorted(por_participante.items()), 1):
        # ocupada — um segmento central por gravação
        for pos in range(1, 18):
            if pos not in posmap:
                continue
            amp = preprocess(load_amplitude(posmap[pos]))
            seg = _segmento_central(amp, seg_len)
            if len(seg) != seg_len:
                continue
            X.append(dtw_features(seg, ref_seg, mask))
            y.append(1)
            meta.append({"participant": p, "position": pos, "label": 1})

        # vazia — n_empty_segments janelas do mesmo comprimento
        if 0 in posmap and posmap[0] != ref_file:
            amp_full = preprocess(load_amplitude(posmap[0]))
            for ini in inicios:
                seg = amp_full[ini:ini + seg_len]
                if len(seg) != seg_len:
                    continue
                X.append(dtw_features(seg, ref_seg, mask))
                y.append(0)
                meta.append({"participant": p, "position": 0, "label": 0})

        if verbose and n % 5 == 0:
            print(f"  {n}/{len(por_participante)} participantes | {len(X)} instâncias")

    return np.array(X), np.array(y), meta
