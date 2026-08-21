"""
Script: Single Config CCDF Analysis
Description: Generates CCDF plot comparing TXOP latencies for a single DB/EB configuration.
Useful for detailed analysis of specific station mix.

File naming convention:
  txop-trace-[DB|EB]-[nDB]-[nEB]-[RTS].csv
  where:
  - [DB|EB]: Station type - DB or EB (which station type's delays are in this file)
  - [nDB]: Total number of DB stations in the simulation
  - [nEB]: Total number of EB stations in the simulation
  - [RTS]: RTS/CTS mode (1=ON, 0=OFF)
  Example: txop-trace-db-2-3-1.csv = DB station delays from simulation with 2 DB + 3 EB stations, RTS/CTS ON

To change the data source: Edit the DATA_DIR path below.
To change station counts: Edit N_DB and N_EB below line 38 and 39.
To adjust X-axis limit: Edit X_LIM based on your data scale.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from plot_config import apply_plot_style, get_cmap, get_colors, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

# Change the data source path here
DATA_DIR = Path("../data/8_15ipt/txop_08_04")

GAP_SECONDS = 1
WARMUP_SECONDS = 30
X_UNIT = "ms"
# Manually adjust X_LIM based on your data scale
X_LIM = (0, 7000)  # Limit for single station config

N_DB = 24
N_EB = 16
# Tip: Comment/uncomment lines below to include/exclude RTS/CTS results
# Remember: last digit in filename = 1 (RTS ON), 0 (RTS OFF)
FILES = [
    # Uncomment to include DB RTS/CTS ON
    ("txop-trace-db-24-16-1.csv", "DB, RTS ON"),
    ("txop-trace-db-24-16-0.csv", "DB, RTS OFF"),
    # Uncomment to include EB RTS/CTS ON and OFF
    ("txop-trace-eb-24-16-1.csv", "EB, RTS ON"),
    ("txop-trace-eb-24-16-0.csv", "EB, RTS OFF"),
]

output_file = f"results/ccdf_nDb{N_DB}_nEb{N_EB}.svg"
colors = get_colors()


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


fig, ax = plt.subplots(figsize=(SUBPLOT_WIDTH, SUBPLOT_HEIGHT))

legend_handles = {}

for filename, label in FILES:
    path = DATA_DIR / filename

    if not path.exists():
        print(f"No file: {path}")
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
        print(f"Dont have proper data in files: {filename}")
        continue

    x, y = compute_ccdf(delays)
    line, = ax.plot(
        x,
        y,
        color=colors[label],
        zorder=3,
        label=label,
        linewidth=1.5,
    )
    legend_handles[label] = line

ax.set_xlim(X_LIM)
ax.set_yscale("log")
ax.minorticks_off()
ax.xaxis.grid(False)
ax.yaxis.grid(True, linewidth=0.9, alpha=0.6)

# Set x-axis ticks every 200 ms
ax.tick_params(axis='x', which='major', labelsize=10)
ax.set_title(f"{N_DB} DB, {N_EB} EB", fontsize=13)
ax.set_yticks([1, 1e-1, 1e-2, 1e-3, 1e-4])
ax.set_yticklabels(["P0", "P90", "P99", "P99.9", "P99.99"],fontsize=10)
ax.set_xlabel(f"Channel access delay [{X_UNIT}]", fontsize=12)
ax.set_ylabel("CCDF", fontsize=12)

ax.legend(
    legend_handles.values(),
    legend_handles.keys(),
    loc="best",
    ncol=1,
    frameon=True,
    fontsize=10,
)


fig.tight_layout()

fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()