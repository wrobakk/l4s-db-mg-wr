"""
Script: CCDF Channel Access Delay Analysis

Description:
Generates CCDF plots of channel access delay measured by TxopAccessTrace
for DB, EB, and one additional VO station across different DB/EB
station configurations.

Expected trace files:
    txop-access-trace-db-NDB-NEB-RTS.csv
    txop-access-trace-eb-NDB-NEB-RTS.csv
    txop-access-trace-vo-NDB-NEB-RTS.csv

RTS value in filename:
    1 -> RTS/CTS enabled
    0 -> RTS/CTS disabled

Expected trace columns:
    txop_start_s,node_id,access_start_ns,delay_ns

Delay definition:
    delay_ns = txop_start_ns - access_start_ns

The delay is already calculated in the ns-3 callback, so the Python
script only filters and converts the stored delay samples.
"""

from math import ceil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_config import (
    apply_plot_style,
    get_colors,
    SUBPLOT_WIDTH,
    SUBPLOT_HEIGHT,
)

apply_plot_style()


# ============================================================
# Configuration
# ============================================================

DATA_DIR = Path("../data/vo_sta_eb/txop_access")
OUTPUT_DIR = Path("results/txop_access/vo_sta_eb")

# Number of regular DB + EB stations.
# The additional VO station is not included in this value.
TOTAL_STA = 40

BASE_START_SECONDS = 0
GAP_SECONDS = 1
WARMUP_SECONDS = 20

X_UNIT = "ms"
X_LIM = (0, 400)

# Label used for the additional station.
# For the low-rate DB scenario, change this to "Low-rate DB".
ADDITIONAL_STA_LABEL = "VO"

RTS_VALUES_TO_PLOT = [True, False]

# configs = [
#     (0, 5),
#     (1, 4),
#     (2, 3),
#     (3, 2),
#     (4, 1),
#     (5, 0),
# ]

# configs = [
#     (0, 10),
#     (2, 8),
#     (4, 6),
#     (6, 4),
#     (8, 2),
#     (10, 0),
# ]

# configs = [
#     (0, 20),
#     (4, 16),
#     (8, 12),
#     (12, 8),
#     (16, 4),
#     (20, 0),
# ]

configs = [
    (0, 40),
    (8, 32),
    (16, 24),
    (24, 16),
    (32, 8),
    (40, 0),
]


# ============================================================
# Plot colors
# ============================================================

colors = get_colors()

fallback_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

fallback_colors = {
    "DB, RTS OFF": fallback_cycle[0],
    "EB, RTS OFF": fallback_cycle[1],
    f"{ADDITIONAL_STA_LABEL}, RTS OFF": "red",
    "DB, RTS ON": fallback_cycle[3],
    "EB, RTS ON": fallback_cycle[4],
    f"{ADDITIONAL_STA_LABEL}, RTS ON": "darkred",
}


def get_line_color(label):
    """
    Return a color from plot_config.py or use a fallback color.
    """
    if label in colors:
        return colors[label]

    return fallback_colors[label]


def get_line_style(rts_enabled):
    """
    Keep the same line style convention as in the existing plots.
    """
    return "-"


# ============================================================
# Data processing
# ============================================================

def get_unit_divisor(unit):
    """
    Convert nanoseconds into the selected output unit.
    """
    if unit == "ns":
        return 1.0
    if unit == "us":
        return 1e3
    if unit == "ms":
        return 1e6
    if unit == "s":
        return 1e9

    raise ValueError(f"Unsupported unit: {unit}")


def compute_cut_time_ns(
    n_db,
    n_eb,
    base_start_s,
    gap_s,
    warmup_s,
):
    """
    Calculate the beginning of the measurement period.

    Startup order in ns-3:
        all regular DB stations,
        all regular EB stations,
        one additional station.

    Additional station start:
        baseStart + (nDbWifi + nEbWifi) * gap

    Measurement starts after the additional station has started
    and the warm-up period has elapsed.
    """
    additional_sta_start_s = (
        base_start_s
        + (n_db + n_eb) * gap_s
    )

    cut_time_s = additional_sta_start_s + warmup_s

    return cut_time_s * 1e9


def load_delays(
    csv_file,
    n_db,
    n_eb,
    base_start_s,
    gap_s,
    warmup_s,
    unit="ms",
):
    """
    Load TxopAccessTrace data.

    Expected columns:
        txop_start_s
        node_id
        access_start_ns
        delay_ns

    The delay has already been calculated in C++:
        delay = txopStart - accessStart
    """
    columns = [
        "txop_start_s",
        "node_id",
        "access_start_ns",
        "delay_ns",
    ]

    try:
        df = pd.read_csv(
            csv_file,
            names=columns,
            header=None,
        )
    except pd.errors.EmptyDataError:
        return np.array([])

    if df.empty:
        return np.array([])

    for column in columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(subset=columns).copy()

    cut_time_ns = compute_cut_time_ns(
        n_db=n_db,
        n_eb=n_eb,
        base_start_s=base_start_s,
        gap_s=gap_s,
        warmup_s=warmup_s,
    )

    # Keep only complete access intervals that started after warm-up.
    df = df[
        df["access_start_ns"] >= cut_time_ns
    ].copy()

    # Remove invalid samples.
    df = df[
        np.isfinite(df["delay_ns"])
        & (df["delay_ns"] >= 0)
    ].copy()

    if df.empty:
        return np.array([])

    delays = (
        df["delay_ns"].to_numpy()
        / get_unit_divisor(unit)
    )

    return np.sort(delays)


def compute_ccdf(delays):
    """
    Compute the empirical complementary cumulative distribution function.
    """
    number_of_samples = len(delays)

    if number_of_samples == 0:
        return np.array([]), np.array([])

    probabilities = (
        1.0
        - np.arange(number_of_samples)
        / number_of_samples
    )

    valid = probabilities > 0

    return delays[valid], probabilities[valid]


# ============================================================
# Trace file selection
# ============================================================

def build_files(n_db, n_eb):
    """
    Build the trace file list for one DB/EB configuration.
    """
    files = []

    for rts_enabled in RTS_VALUES_TO_PLOT:
        rts_value = 1 if rts_enabled else 0
        rts_label = "RTS ON" if rts_enabled else "RTS OFF"

        if n_db > 0:
            files.append({
                "filename": (
                    f"txop-access-trace-db-"
                    f"{n_db}-{n_eb}-{rts_value}.csv"
                ),
                "label": f"DB, {rts_label}",
                "rts_enabled": rts_enabled,
            })

        if n_eb > 0:
            files.append({
                "filename": (
                    f"txop-access-trace-eb-"
                    f"{n_db}-{n_eb}-{rts_value}.csv"
                ),
                "label": f"EB, {rts_label}",
                "rts_enabled": rts_enabled,
            })

        files.append({
            "filename": (
                f"txop-access-trace-vo-"
                f"{n_db}-{n_eb}-{rts_value}.csv"
            ),
            "label": f"{ADDITIONAL_STA_LABEL}, {rts_label}",
            "rts_enabled": rts_enabled,
        })

    return files


# ============================================================
# Plot generation
# ============================================================

number_of_columns = 3
number_of_rows = ceil(len(configs) / number_of_columns)

fig, axes = plt.subplots(
    number_of_rows,
    number_of_columns,
    figsize=(
        number_of_columns * SUBPLOT_WIDTH,
        number_of_rows * SUBPLOT_HEIGHT,
    ),
    squeeze=False,
)

axes = axes.flatten()

for axis_index, (n_db, n_eb) in enumerate(configs):
    ax = axes[axis_index]
    files = build_files(n_db, n_eb)

    plotted_anything = False

    for file_info in files:
        filename = file_info["filename"]
        label = file_info["label"]
        rts_enabled = file_info["rts_enabled"]

        path = DATA_DIR / filename

        if not path.exists():
            print(f"No file: {path}")
            continue

        delays = load_delays(
            csv_file=path,
            n_db=n_db,
            n_eb=n_eb,
            base_start_s=BASE_START_SECONDS,
            gap_s=GAP_SECONDS,
            warmup_s=WARMUP_SECONDS,
            unit=X_UNIT,
        )

        if len(delays) == 0:
            print(f"No proper data in file: {filename}")
            continue

        x, y = compute_ccdf(delays)

        ax.plot(
            x,
            y,
            color=get_line_color(label),
            linestyle=get_line_style(rts_enabled),
            linewidth=1.5,
            zorder=3,
            label=label,
        )

        plotted_anything = True

    ax.set_title(
        f"{n_db} DB, {n_eb} EB, 1 {ADDITIONAL_STA_LABEL} STA"
    )

    ax.set_yscale("log")
    ax.set_xlim(*X_LIM)

    ax.minorticks_off()
    ax.xaxis.grid(False)
    ax.yaxis.grid(
        True,
        linewidth=0.9,
        alpha=0.6,
    )

    ax.set_yticks([
        1,
        1e-1,
        1e-2,
        1e-3,
        1e-4,
    ])

    ax.set_yticklabels([
        "P0",
        "P90",
        "P99",
        "P99.9",
        "P99.99",
    ], fontsize=10)

    ax.set_xlabel(
        f"Channel access delay [{X_UNIT}]",
        fontsize=10,
    )

    ax.tick_params(
        axis="x",
        labelsize=10,
    )

    ax.set_ylabel(
        "CCDF",
        fontsize=10,
    )

    if plotted_anything:
        ax.legend(
            loc="best",
            ncol=1,
            frameon=True,
            fontsize=8,
        )

# Hide unused subplot axes.
for axis_index in range(len(configs), len(axes)):
    axes[axis_index].set_visible(False)

fig.tight_layout()

output_file = (
    OUTPUT_DIR
    / (
        f"ccdf_txop_access_{TOTAL_STA}sta.png"
    )
)

fig.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight",
)

print(f"Saved plot: {output_file}")

plt.show()