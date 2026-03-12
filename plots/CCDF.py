import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

DATA_DIR = Path("../data/txop")

N_DB = 12
N_EB = 8
GAP_SECONDS = 1
WARMUP_SECONDS = 30
X_UNIT = "ms"

FILES = [
    ("txop-trace-db-12-8-1.csv", "DB, RTS on"),
    ("txop-trace-db-12-8-0.csv", "DB, RTS off"),
    ("txop-trace-eb-12-8-1.csv", "EB, RTS on"),
    ("txop-trace-eb-12-8-0.csv", "EB, RTS off"),
]

OUTPUT_FILE = "ccdf_access_delay_12_8.png"


def get_unit_divisor(unit):
    if unit == "ns":
        return 1.0
    if unit == "us":
        return 1e3
    if unit == "ms":
        return 1e6
    if unit == "s":
        return 1e9
    raise ValueError(f"Unsupported unit: {unit}")


def compute_cut_time_ns(n_db, n_eb, gap_s, warmup_s):
    n_stations = n_db + n_eb
    cut_time_s = n_stations * gap_s + warmup_s
    return cut_time_s * 1e9


def load_delays(csv_file, n_db, n_eb, gap_s, warmup_s, unit="ms"):
    cols = ["time_s", "node_id", "start_ns", "duration_ns", "success"]
    df = pd.read_csv(csv_file, names=cols)

    # 0 == udany TXOP
    df = df[df["success"] == 0].copy()

    cut_time_ns = compute_cut_time_ns(n_db, n_eb, gap_s, warmup_s)
    df = df[df["start_ns"] >= cut_time_ns].copy()

    if df.empty:
        return np.array([])

    df["end_ns"] = df["start_ns"] + df["duration_ns"]
    df = df.sort_values(["node_id", "start_ns"]).copy()
    df["prev_end_ns"] = df.groupby("node_id")["end_ns"].shift(1)
    df["delay_ns"] = df["start_ns"] - df["prev_end_ns"]

    df = df.dropna(subset=["prev_end_ns"]).copy()
    df = df[df["delay_ns"] >= 0].copy()

    if df.empty:
        return np.array([])

    return np.sort(df["delay_ns"].to_numpy() / get_unit_divisor(unit))


def compute_ccdf(delays):
    n = len(delays)
    if n == 0:
        return np.array([]), np.array([])

    y = 1.0 - np.arange(n) / n
    mask = y > 0
    return delays[mask], y[mask]


colors = get_cmap(4)

fig, ax = plt.subplots(figsize=(SUBPLOT_WIDTH, SUBPLOT_HEIGHT))

for (filename, label), color in zip(FILES, colors):
    path = DATA_DIR / filename

    if not path.exists():
        print(f"Brak pliku: {path}")
        continue

    delays = load_delays(
        csv_file=path,
        n_db=N_DB,
        n_eb=N_EB,
        gap_s=GAP_SECONDS,
        warmup_s=WARMUP_SECONDS,
        unit=X_UNIT,
    )

    if len(delays) == 0:
        print(f"Brak poprawnych danych po filtracji: {filename}")
        continue

    x, y = compute_ccdf(delays)
    ax.plot(
        x,
        y,
        color=color,
        zorder=3,
        label=label,
    )

ax.set_yscale("log")
ax.set_xlabel(f"Channel access delay [{X_UNIT}]")
ax.set_ylabel("CCDF")
ax.grid(True, which="both", zorder=0)

ax.set_yticks([1, 1e-1, 1e-2, 1e-3, 1e-4])
ax.set_yticklabels(["P0", "P90", "P99", "P99.9", "P99.99"])

fig.suptitle(
    "CCDF of channel access delay for" f"{N_DB + N_EB} STAs ({N_DB} DB, {N_EB} EB)" "stations with RTS on/off, "
    "IEEE 802.11ax, MCS 11, 20 MHz, GI 800 ns, payload 1450 B, "
    "offered load 150 Mb/s per station, staggered startup (1 STA/s), "
    "warm-up 30 s after the last start, total simulation time 200 s"
)


fig.legend()
fig.tight_layout(rect=[0, 0.08, 1, 0.92])
plt.show()