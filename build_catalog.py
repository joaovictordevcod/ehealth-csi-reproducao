"""
build_catalog.py  —  eHealth CSI (DS2)

Indexa os arquivos .npz do dataset e monta um banco SQLite navegável,
já com os códigos de posição e o cruzamento com valid.txt.

Uso:
    python3 build_catalog.py /caminho/do/dataset catalogo.db [valid.txt]

Depois:
    pip install datasette
    datasette catalogo.db
"""
import sys
import sqlite3
import re
import numpy as np
from pathlib import Path

# Códigos de posição — README_eHealth.md
POSICOES = {
    0:  ("ausencia",  "Ausência de pessoa (sala vazia)"),
    1:  ("sentado",   "Sentado de frente, respiração normal"),
    2:  ("sentado",   "Sentado de frente, respiração intermitente"),
    3:  ("transicao", "Senta e levanta (a cada 10 s), respiração normal"),
    4:  ("sentado",   "Sentado de costas, respiração normal"),
    5:  ("sentado",   "Sentado de costas, respiração intermitente"),
    6:  ("em_pe",     "Em pé de frente, respiração normal"),
    7:  ("em_pe",     "Em pé de frente, respiração intermitente"),
    8:  ("em_pe",     "Em pé de costas, respiração normal"),
    9:  ("em_pe",     "Em pé de costas, respiração intermitente"),
    10: ("deitado",   "Deitado de barriga para cima, respiração normal"),
    11: ("deitado",   "Deitado de barriga para cima, respiração intermitente"),
    12: ("deitado",   "Deitado de bruços, respiração normal"),
    13: ("deitado",   "Deitado de bruços, respiração intermitente"),
    14: ("transicao", "Deita e levanta (a cada 20 s), respiração normal"),
    15: ("movimento", "Caminhando, respiração normal"),
    16: ("movimento", "Correndo, respiração normal"),
    17: ("movimento", "Varrendo, respiração normal"),
    18: ("queda",     "Em pé e queda (20 s e 40 s), respiração normal"),
}

FNAME_RE = re.compile(
    r"(?P<position>\d+)_(?P<date>\d{4}_\d{2}_\d{2})_-_(?P<time>\d{2}_\d{2}_\d{2})"
    r"_bw_(?P<bw>\d+)_ch_(?P<ch>\d+)\.npz$"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant INTEGER,
    position INTEGER,
    position_group TEXT,
    position_label TEXT,
    is_empty_room INTEGER,
    breathing TEXT,
    valid_flag TEXT,
    date TEXT,
    time TEXT,
    bandwidth_mhz INTEGER,
    channel INTEGER,
    file_path TEXT UNIQUE,
    file_size_mb REAL,
    n_packets INTEGER,
    n_subcarriers INTEGER,
    duration_s REAL,
    rate_mean_hz REAL,
    dt_mean_ms REAL,
    dt_std_ms REAL,
    anomalous_subcarriers INTEGER,
    amp_median REAL,
    has_nan INTEGER,
    parse_error TEXT
);
"""


def load_valid(valid_path):
    """Lê valid.txt -> {(participante, posicao): 'o'|'m'}"""
    flags = {}
    if not valid_path or not Path(valid_path).exists():
        return flags
    with open(valid_path) as fh:
        header = fh.readline().strip().strip(";").split(";")
        cols = header[1:]
        for line in fh:
            parts = line.strip().strip(";").split(";")
            if not parts or not parts[0].isdigit():
                continue
            p = int(parts[0])
            for c, v in zip(cols, parts[1:]):
                if c.isdigit():
                    flags[(p, int(c))] = v
    return flags


def guess_participant(path: Path, root: Path):
    """Procura, nas pastas acima do arquivo, um nome puramente numérico
    (padrão do dataset: scans/000/, scans/001/ ...)."""
    for part in reversed(path.relative_to(root).parts[:-1]):
        if part.isdigit():
            return int(part)
    return None


def index_file(path: Path, root: Path, flags: dict) -> dict:
    row = {k: None for k in (
        "participant", "position", "position_group", "position_label",
        "is_empty_room", "breathing", "valid_flag", "date", "time",
        "bandwidth_mhz", "channel", "n_packets", "n_subcarriers",
        "duration_s", "rate_mean_hz", "dt_mean_ms", "dt_std_ms",
        "anomalous_subcarriers", "amp_median", "has_nan", "parse_error")}
    row["file_path"] = str(path)
    row["file_size_mb"] = round(path.stat().st_size / 1e6, 3)
    row["participant"] = guess_participant(path, root)

    m = FNAME_RE.search(path.name)
    if m:
        pos = int(m.group("position"))
        grupo, label = POSICOES.get(pos, ("desconhecida", "código não documentado"))
        row.update(
            position=pos, position_group=grupo, position_label=label,
            is_empty_room=int(pos == 0),
            breathing=("intermitente" if "intermitente" in label
                       else ("normal" if "normal" in label else None)),
            date=m.group("date").replace("_", "-"),
            time=m.group("time").replace("_", ":"),
            bandwidth_mhz=int(m.group("bw")), channel=int(m.group("ch")),
        )
        if row["participant"] is not None:
            row["valid_flag"] = flags.get((row["participant"], pos))
    else:
        row["parse_error"] = "nome fora do padrão esperado"

    try:
        d = np.load(path, allow_pickle=True)
        csi, ts = d["csi"], d["ts"]
        n_pkts, n_sub = csi.shape
        duration = float(ts[-1] - ts[0]) if n_pkts > 1 else 0.0
        dt = np.diff(ts) if n_pkts > 1 else np.array([0.0])
        amp = np.abs(csi)
        mean_amp = amp.mean(axis=0)
        med = float(np.median(mean_amp))

        row.update(
            n_packets=n_pkts, n_subcarriers=n_sub,
            duration_s=round(duration, 3),
            rate_mean_hz=round(n_pkts / duration, 3) if duration > 0 else None,
            dt_mean_ms=round(float(dt.mean()) * 1000, 3),
            dt_std_ms=round(float(dt.std()) * 1000, 3),
            anomalous_subcarriers=int((mean_amp > 5 * med).sum()),
            amp_median=round(med, 3),
            has_nan=int(bool(np.isnan(csi.real).any() or np.isnan(csi.imag).any())),
        )
    except Exception as e:
        row["parse_error"] = (row["parse_error"] or "") + f" | erro ao ler: {e}"

    return row


def build(root_dir, db_path, valid_path=None):
    root = Path(root_dir)
    flags = load_valid(valid_path)
    if flags:
        print(f"valid.txt carregado: {len(flags)} marcações")

    files = sorted(root.rglob("*.npz"))
    print(f"{len(files)} arquivos .npz encontrados em {root}")
    if not files:
        print("nada encontrado — confira o caminho.")
        return

    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()

    cols = insert_sql = None
    n_err = 0
    for i, f in enumerate(files, 1):
        row = index_file(f, root, flags)
        if cols is None:
            cols = list(row.keys())
            insert_sql = (f"INSERT OR REPLACE INTO recordings ({','.join(cols)}) "
                          f"VALUES ({','.join('?' * len(cols))})")
        conn.execute(insert_sql, [row[c] for c in cols])
        if row["parse_error"]:
            n_err += 1
        if i % 200 == 0:
            conn.commit()
            print(f"  {i}/{len(files)}...")

    conn.commit()

    print(f"\nindexados: {len(files)} | com problema: {n_err}")
    cur = conn.cursor()
    for q, label in [
        ("SELECT COUNT(DISTINCT participant) FROM recordings", "participantes"),
        ("SELECT COUNT(*) FROM recordings WHERE is_empty_room=1", "gravações de sala vazia"),
        ("SELECT COUNT(*) FROM recordings WHERE is_empty_room=0", "gravações com pessoa"),
        ("SELECT ROUND(AVG(rate_mean_hz),2) FROM recordings", "taxa média (Hz)"),
        ("SELECT ROUND(AVG(n_packets),0) FROM recordings", "pacotes por arquivo (média)"),
    ]:
        try:
            print(f"  {label}: {cur.execute(q).fetchone()[0]}")
        except Exception:
            pass
    conn.close()
    print(f"\nbanco salvo em: {db_path}\nabra com:  datasette {db_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    build(sys.argv[1],
          sys.argv[2] if len(sys.argv) > 2 else "catalogo.db",
          sys.argv[3] if len(sys.argv) > 3 else None)
