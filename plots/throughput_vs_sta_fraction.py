"""
Script: Throughput Ratio Plot
Description: Generates a 2x2 subplot visualization comparing throughput per station
across different total STA counts (5, 10, 20, 40) with varying DB/EB fractions
and RTS/CTS settings.

To change the data source: Edit the read_csv() path below to point to your desired CSV file.
Rts/CTS ON and OFF results can be toggled by commenting out one of the plot blocks in the loop (see line 62).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

<<<<<<< HEAD:plots/throughput_vs_sta_fraction.py
# Change the data source path here
df = pd.read_csv("../data/10_15ipt/throughput.csv")
=======
df = pd.read_csv("../data/7_ipt/throughput.csv")
>>>>>>> 8a94839 (Adding x+ipt and initial and intermediate backoff):plots/throughput_ratio_plot.py


df["enableRts"] = df["enableRts"].astype(str).str.strip().map({
    "1": True,
    "0": False
})


df["totalSta"] = df["nDbWifi"] + df["nEbWifi"]
df["fractionDb"] = df["nDbWifi"] / df["totalSta"]


df.loc[df["nDbWifi"] == 0, "throughputBSS_DB"] = np.nan
df.loc[df["nEbWifi"] == 0, "throughputBSS_EB"] = np.nan

totals = [5, 10, 20, 40]
colors = get_cmap(4)
y_locators = [5, 3, 2, 1]  # Different MultipleLocator per subplot: total=5, 10, 20, 40
y_limits = [30, 18, 10, 5]  # Different y-axis limits per subplot: total=5, 10, 20, 40

nrows, ncols = 2, 2
fig, axes = plt.subplots(
    nrows,
    ncols,
    figsize=(ncols * SUBPLOT_WIDTH, nrows * SUBPLOT_HEIGHT)
)

axes = axes.flatten()

for i, total in enumerate(totals):
    ax = axes[i]
    d = df[df["totalSta"] == total].copy()


    y1 = d["throughputBSS_DB"] / d["nDbWifi"].replace(0, np.nan)
    y2 = d["throughputBSS_EB"] / d["nEbWifi"].replace(0, np.nan)
    
    d_rts_on = d[d["enableRts"] == True].sort_values("fractionDb")
    d_rts_off = d[d["enableRts"] == False].sort_values("fractionDb")

<<<<<<< HEAD:plots/throughput_vs_sta_fraction.py
    # Tip: Comment out one of the plot blocks below to show only RTS/CTS ON or only RTS/CTS OFF results
    
    # DB with RTS/CTS ON
=======
>>>>>>> 8a94839 (Adding x+ipt and initial and intermediate backoff):plots/throughput_ratio_plot.py
    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_DB"] / d_rts_on["nDbWifi"].replace(0, np.nan),
        color=colors[0], marker="o", zorder=3, label="DB, RTS/CTS ON",
    )

    # DB with RTS/CTS OFF
    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_DB"] / d_rts_off["nDbWifi"].replace(0, np.nan),
        color=colors[1], marker="s", zorder=3, label="DB, RTS/CTS OFF",
    )

<<<<<<< HEAD:plots/throughput_vs_sta_fraction.py
    # EB with RTS/CTS ON
=======
>>>>>>> 8a94839 (Adding x+ipt and initial and intermediate backoff):plots/throughput_ratio_plot.py
    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_EB"] / d_rts_on["nEbWifi"].replace(0, np.nan),
        color=colors[2], marker="o", zorder=3, label="EB, RTS/CTS ON",
    )

    # EB with RTS/CTS OFF
    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_EB"] / d_rts_off["nEbWifi"].replace(0, np.nan),
        color=colors[3], marker="s", zorder=3, label="EB, RTS/CTS OFF",

    )
    
    ax.set_xlabel("Fraction of DB STAs")
    ax.set_ylabel("Throughput per station [Mbit/s]")
    ax.set_title(f"{total} STAs")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, y_limits[i])

    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])

    ax.yaxis.set_major_locator(MultipleLocator(y_locators[i]))
    ax.minorticks_off()
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, linewidth=0.9, alpha=0.6)
    
    ax.legend(
        loc="lower left",
        ncol=1,
        frameon=True,
    )


fig.suptitle("7 + 1.5*ipt")
fig.tight_layout()

plt.savefig("results/throughput7_15ipt_ratio.svg")
plt.show()