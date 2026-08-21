"""
Script: Throughput Ratio Plot

Description:
Generates a 2x2 subplot visualization comparing throughput per station
for total STA counts equal to 5, 10, 20, and 40.

Data sources:
- 5 and 10 STAs: b = 8, m = 1.5
- 20 and 40 STAs: b = 9, m = 1.5
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from plot_config import (
    apply_plot_style,
    get_cmap,
    SUBPLOT_WIDTH,
    SUBPLOT_HEIGHT,
)

apply_plot_style()


def prepare_dataframe(csv_path):
    """Load the CSV file and calculate helper columns."""

    dataframe = pd.read_csv(csv_path)

    # Uncomment this block if enableRts is stored as 0/1 strings.
    dataframe["enableRts"] = (
        dataframe["enableRts"]
        .astype(str)
        .str.strip()
        .map({
            "1": True,
            "0": False,
            "True": True,
            "False": False,
        })
    )

    dataframe["totalSta"] = (
        dataframe["nDbWifi"] + dataframe["nEbWifi"]
    )

    dataframe["fractionDb"] = (
        dataframe["nDbWifi"] / dataframe["totalSta"]
    )

    dataframe.loc[
        dataframe["nDbWifi"] == 0,
        "throughputBSS_DB"
    ] = np.nan

    dataframe.loc[
        dataframe["nEbWifi"] == 0,
        "throughputBSS_EB"
    ] = np.nan

    return dataframe


# Parameters b = 8, m = 1.5
df_small = prepare_dataframe(
    "../data/8_15ipt/throughput.csv"
)

# Parameters b = 9, m = 1.5
df_large = prepare_dataframe(
    "../data/9_15ipt/throughput.csv"
)


# Take 5 and 10 STA scenarios from the first file.
df_small = df_small[
    df_small["totalSta"].isin([5])
].copy()

# Take 20 and 40 STA scenarios from the second file.
df_large = df_large[
    df_large["totalSta"].isin([10, 20, 40])
].copy()

# Combine selected scenarios into one dataframe.
df = pd.concat(
    [df_small, df_large],
    ignore_index=True
)


totals = [5, 10, 20, 40]

colors = get_cmap(4)

y_locators = [5, 3, 2, 1]
y_limits = [30, 18, 10, 5]

nrows = 2
ncols = 2

fig, axes = plt.subplots(
    nrows,
    ncols,
    figsize=(
        ncols * SUBPLOT_WIDTH,
        nrows * SUBPLOT_HEIGHT,
    ),
)

axes = axes.flatten()


for i, total in enumerate(totals):
    ax = axes[i]

    d = df[
        df["totalSta"] == total
    ].copy()

    d_rts_on = d[
        d["enableRts"] == True
    ].sort_values("fractionDb")

    d_rts_off = d[
        d["enableRts"] == False
    ].sort_values("fractionDb")

    # DB with RTS/CTS ON
    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_DB"]
        / d_rts_on["nDbWifi"].replace(0, np.nan),
        color=colors[0],
        marker="o",
        zorder=3,
        label="DB, RTS/CTS ON",
    )

    # DB with RTS/CTS OFF
    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_DB"]
        / d_rts_off["nDbWifi"].replace(0, np.nan),
        color=colors[1],
        marker="s",
        zorder=3,
        label="DB, RTS/CTS OFF",
    )

    # EB with RTS/CTS ON
    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_EB"]
        / d_rts_on["nEbWifi"].replace(0, np.nan),
        color=colors[2],
        marker="o",
        zorder=3,
        label="EB, RTS/CTS ON",
    )

    # EB with RTS/CTS OFF
    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_EB"]
        / d_rts_off["nEbWifi"].replace(0, np.nan),
        color=colors[3],
        marker="s",
        zorder=3,
        label="EB, RTS/CTS OFF",
    )

    ax.set_xlabel("Fraction of DB STAs", fontsize=12)
    ax.set_ylabel("Throughput per station [Mbit/s]", fontsize=12)
    ax.set_title(f"{total} STAs", fontsize=13)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, y_limits[i])

    ax.set_xticks([
        0.0,
        0.2,
        0.4,
        0.6,
        0.8,
        1.0,
    ])

    ax.set_xticklabels([
        "0",
        "0.2",
        "0.4",
        "0.6",
        "0.8",
        "1",
    ], fontsize=11)

    ax.yaxis.set_major_locator(
        MultipleLocator(y_locators[i])
    )
    ax.tick_params(axis='y', labelsize=11)

    ax.minorticks_off()
    ax.xaxis.grid(False)
    ax.yaxis.grid(
        True,
        linewidth=0.9,
        alpha=0.6,
    )

    ax.legend(
        loc="lower left",
        ncol=1,
        frameon=True,
        fontsize=10,
    )


fig.tight_layout()

plt.savefig(
    "results/throughput_best_parameters_ratio.svg"
)

plt.show()