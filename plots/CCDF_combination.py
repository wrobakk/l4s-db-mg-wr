import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

DATA_DIR = Path("../data/9_15ipt/txop_20_04")
TOTAL_STA = 40
GAP_SECONDS = 1
WARMUP_SECONDS =30
X_UNIT = "ms"
X_LIM = (0, 7000) # 5 - 2000; 10 - 3500; 20 - 6000; 40 - 14000 

#configs = [(0, 5), (1, 4), (2, 3), (3, 2), (4, 1), (5, 0)]  # 5 STAs
#configs = [(0, 10), (2, 8), (4, 6), (6, 4), (8, 2), (10, 0)]  # 10 STAs
#configs = [(0, 20), (4, 16), (8, 12), (12, 8), (16, 4), (20, 0)]  # 20 STAs
configs = [(0, 40), (8, 32), (16, 24), (24, 16), (32, 8), (40, 0)]  # 40 STAs

colors = {
    "DB, RTS ON": get_cmap(4)[0],
    "DB, RTS OFF": get_cmap(4)[1],
    "EB, RTS ON": get_cmap(4)[2],
    "EB, RTS OFF": get_cmap(4)[3],
}


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

    # 0 == successful TXOP
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


def build_files(n_db, n_eb):
    files = []

    if n_db > 0:
        files.append((f"txop-trace-db-{n_db}-{n_eb}-1.csv", "DB, RTS ON"))
        files.append((f"txop-trace-db-{n_db}-{n_eb}-0.csv", "DB, RTS OFF"))

    if n_eb > 0:
        files.append((f"txop-trace-eb-{n_db}-{n_eb}-1.csv", "EB, RTS ON"))
        files.append((f"txop-trace-eb-{n_db}-{n_eb}-0.csv", "EB, RTS OFF"))

    return files


fig, axes = plt.subplots(
    2, 3,
    figsize=(3 * SUBPLOT_WIDTH, 2.6 * SUBPLOT_HEIGHT),
)
axes = axes.flatten()

legend_handles = {}

for ax, (n_db, n_eb) in zip(axes, configs):
    files = build_files(n_db, n_eb)

    for filename, label in files:
        path = DATA_DIR / filename

        if not path.exists():
            print(f"No file: {path}")
            continue

        delays = load_delays(
            csv_file=path,
            n_db=n_db,
            n_eb=n_eb,
            gap_s=GAP_SECONDS,
            warmup_s=WARMUP_SECONDS,
            unit=X_UNIT,
        )

        if len(delays) == 0:
            print(f"Dont have proper data in files: {filename}")
            continue

        x, y = compute_ccdf(delays)
        line, = ax.plot(
            x,
            y,
            color=colors[label],
            zorder=3,
            label=label,
        )

        if label not in legend_handles:
            legend_handles[label] = line

    ax.set_title(f"{n_db} DB, {n_eb} EB")
    ax.set_yscale("log")
    ax.set_xlim(*X_LIM)
    ax.grid(True, which="both", zorder=0)

    ax.set_yticks([1, 1e-1, 1e-2, 1e-3, 1e-4])
    ax.set_yticklabels(["P0", "P90", "P99", "P99.9", "P99.99"])
    ax.set_xlabel(f"Channel access delay [{X_UNIT}]")
    ax.set_ylabel("CCDF")
    
    ax.legend(
    #legend_handles.values(),
    #legend_handles.keys(),
    loc="best",
    ncol=1,
    frameon=True,
)


fig.suptitle(
    "CCDF of channel access delay for "f"{TOTAL_STA}" " stations, staggered startup (1 STA/s), warm-up 30 s after the last start, total simulation time 200 s, \n"
    "\n$\\mathbf{Deterministic \\: backoff = 9 + 1.5*ipt}$"
)



fig.tight_layout(rect=[0, 0.08, 1, 0.95])

output_file = f"ccdf_{TOTAL_STA}sta_all_ratios.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()