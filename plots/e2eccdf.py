"""
Script: CCDF TX/RX Delay Analysis

Description:
Generates CCDF plots comparing MAC end-to-end packet delay for DB, EB,
and one additional low-rate DB station across different DB/EB station
configurations.

The additional low-rate station is still identified as "VO" in TX records,
but it belongs to the DB BSS, uses AC_BE, and has Deterministic Backoff enabled.

Expected trace files:
    txrx-NDB-NEB-RTS.csv

RTS value in filename:
    1 -> RTS/CTS enabled
    0 -> RTS/CTS disabled

Expected trace columns:
    time,event,group,nodeId,packetUid

Delay definition:
    delay = first MacRx time - first MacTx time
    for the same packetUid.

To change the data source:
    Edit DATA_DIR.

To change the number of stations:
    Edit TOTAL_STA and configs.

To select RTS/CTS results:
    Edit RTS_VALUES_TO_PLOT:
        [False]        -> RTS OFF only
        [True]         -> RTS ON only
        [True, False]  -> both
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

DATA_DIR = Path("../data/vo_sta_eb/txrx")
OUTPUT_DIR = Path("results/txrx")

TOTAL_STA = 20

BASE_START_SECONDS = 0
GAP_SECONDS = 1
WARMUP_SECONDS = 30

X_UNIT = "ms"
X_LIM = (0, 250)

# Select which RTS configurations should be plotted.
RTS_VALUES_TO_PLOT = [True, False]

configs = [
    (0, 5),
    (1, 4),
    (2, 3),
    (3, 2),
    (4, 1),
    (5, 0),
]

configs = [
    (0, 10),
    (2, 8),
    (4, 6),
    (6, 4),
    (8, 2),
    (10, 0),
]

configs = [
    (0, 20),
    (4, 16),
    (8, 12),
    (12, 8),
    (16, 4),
    (20, 0),
]

# configs = [
#     (0, 40),
#     (8, 32),
#     (16, 24),
#     (24, 16),
#     (32, 8),
#     (40, 0),
# ]


# ============================================================
# Plot colors
# ============================================================

colors = get_colors()

fallback_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

fallback_colors = {
    "DB, RTS OFF": fallback_cycle[0],
    "EB, RTS OFF": fallback_cycle[1],
    "VO, RTS OFF": "red",
    "DB, RTS ON": fallback_cycle[3],
    "EB, RTS ON": fallback_cycle[4],
    "VO, RTS ON": "darkred",
}


def get_line_color(label):
    """
    Return the color from plot_config.py.
    If the label is not defined there, use a fallback color.
    """
    return colors.get(label, fallback_colors[label])


def get_line_style(rts_enabled):
    """
    Use different line styles when both RTS ON and RTS OFF
    are shown on the same plot.
    """
    return "-" if rts_enabled else "-"


# ============================================================
# Data processing
# ============================================================

def get_unit_multiplier(unit):
    """
    Convert seconds into the selected output unit.
    """
    if unit == "s":
        return 1.0
    if unit == "ms":
        return 1e3
    if unit == "us":
        return 1e6
    if unit == "ns":
        return 1e9

    raise ValueError(f"Unsupported unit: {unit}")


def compute_cut_time_s(
    n_db,
    n_eb,
    base_start_s,
    gap_s,
    warmup_s,
):
    """
    Calculate the beginning of the measurement period.

    Startup order in ns-3:
        all regular DB stations
        all EB stations
        one additional low-rate DB station

    Additional station start time:
        baseStart + (nDbWifi + nEbWifi) * gap

    Measurement begins after that station has started
    and the warm-up period has elapsed.
    """
    low_rate_start_s = (
        base_start_s
        + (n_db + n_eb) * gap_s
    )

    return low_rate_start_s + warmup_s


def load_txrx(csv_file):
    """
    Load a TX/RX trace file.

    Expected columns:
        time
        event
        group
        nodeId
        packetUid

    Example:
        35.002,TX,VO,5,500
        35.006,RX,DB,11,500

    Files with and without a header are supported.
    """
    columns = [
        "time",
        "event",
        "group",
        "nodeId",
        "packetUid",
    ]

    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)

    if not set(columns).issubset(df.columns):
        try:
            df = pd.read_csv(
                csv_file,
                names=columns,
                header=None,
            )
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=columns)

    df = df[columns].copy()

    df["time"] = pd.to_numeric(
        df["time"],
        errors="coerce",
    )
    df["nodeId"] = pd.to_numeric(
        df["nodeId"],
        errors="coerce",
    )
    df["packetUid"] = pd.to_numeric(
        df["packetUid"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "time",
            "event",
            "group",
            "nodeId",
            "packetUid",
        ]
    ).copy()

    df["event"] = (
        df["event"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["group"] = (
        df["group"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["nodeId"] = df["nodeId"].astype(int)
    df["packetUid"] = df["packetUid"].astype(int)

    return df


def load_delays(
    df,
    group,
    n_db,
    n_eb,
    base_start_s,
    gap_s,
    warmup_s,
    unit="ms",
):
    """
    Calculate MAC end-to-end packet delay for one TX group.

    Delay:
        first MacRx - first MacTx
        for the same packetUid.

    Packet class is determined from the TX record:
        DB -> regular DB station
        EB -> regular EB station
        VO -> additional low-rate DB station

    RX records are not filtered by group because the AP records:
        RX,DB for both regular DB and low-rate DB traffic,
        RX,EB for regular EB traffic.
    """
    if df.empty:
        return np.array([])

    cut_time_s = compute_cut_time_s(
        n_db=n_db,
        n_eb=n_eb,
        base_start_s=base_start_s,
        gap_s=gap_s,
        warmup_s=warmup_s,
    )

    tx = df[
        (df["event"] == "TX")
        & (df["group"] == group)
        & (df["time"] >= cut_time_s)
    ][
        ["packetUid", "time"]
    ].copy()

    rx = df[
        df["event"] == "RX"
    ][
        ["packetUid", "time"]
    ].copy()

    if tx.empty or rx.empty:
        return np.array([])

    # Use the first TX and first RX occurrence for every packet UID.
    tx = (
        tx.groupby("packetUid", as_index=False)["time"]
        .min()
        .rename(columns={"time": "tx_time"})
    )

    rx = (
        rx.groupby("packetUid", as_index=False)["time"]
        .min()
        .rename(columns={"time": "rx_time"})
    )

    matched = tx.merge(
        rx,
        on="packetUid",
        how="inner",
        validate="one_to_one",
    )

    if matched.empty:
        return np.array([])

    matched["delay_s"] = (
        matched["rx_time"]
        - matched["tx_time"]
    )

    matched = matched[
        matched["delay_s"] >= 0
    ].copy()

    if matched.empty:
        return np.array([])

    delays = (
        matched["delay_s"].to_numpy()
        * get_unit_multiplier(unit)
    )

    return np.sort(delays)


def compute_ccdf(delays):
    """
    Compute the empirical complementary cumulative
    distribution function.
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
    Build the list of TX/RX trace files for one subplot.

    One TX/RX file contains DB, EB, and VO records.
    """
    files = []

    for rts_enabled in RTS_VALUES_TO_PLOT:
        rts_value = 1 if rts_enabled else 0

        files.append({
            "filename": (
                f"txrx-"
                f"{n_db}-{n_eb}-{rts_value}.csv"
            ),
            "rts_enabled": rts_enabled,
        })

    return files


def build_groups(n_db, n_eb):
    """
    Select the packet groups available in one scenario.
    """
    groups = []

    if n_db > 0:
        groups.append("DB")

    if n_eb > 0:
        groups.append("EB")

    # The additional low-rate DB station exists in every scenario.
    groups.append("VO")

    return groups


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
    groups = build_groups(n_db, n_eb)

    plotted_anything = False

    for file_info in files:
        filename = file_info["filename"]
        rts_enabled = file_info["rts_enabled"]
        rts_label = "RTS ON" if rts_enabled else "RTS OFF"

        path = DATA_DIR / filename

        if not path.exists():
            print(f"No file: {path}")
            continue

        df = load_txrx(path)

        if df.empty:
            print(f"No proper data in file: {filename}")
            continue

        for group in groups:
            label = f"{group}, {rts_label}"

            delays = load_delays(
                df=df,
                group=group,
                n_db=n_db,
                n_eb=n_eb,
                base_start_s=BASE_START_SECONDS,
                gap_s=GAP_SECONDS,
                warmup_s=WARMUP_SECONDS,
                unit=X_UNIT,
            )

            if len(delays) == 0:
                print(
                    f"No matched {group} TX/RX data "
                    f"in file: {filename}"
                )
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
        f"{n_db} DB, {n_eb} EB, 1 VO DB STA"
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
        f"MAC end-to-end delay [{X_UNIT}]",
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

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

output_file = (
    OUTPUT_DIR
    / f"ccdf_txrx_{TOTAL_STA}be_sta_plus_vo_VO.png"
)

fig.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight",
)

print(f"Saved plot: {output_file}")

plt.show()