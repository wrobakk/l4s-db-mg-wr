"""
Single STA Count Throughput Ratio Analysis
Description: Generates a single plot comparing per-station throughput for a fixed STA count
across DB/EB fractions and RTS/CTS settings.

To change the data source: Edit the read_csv() path below to point to your desired CSV file.
To change the STA count: Edit the TOTAL_STA variable below, line 28 to the desired total number of STAs ( 5, 10, 20, 40).
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from plot_config import apply_plot_style, get_colors, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

# Change the data source path here
df = pd.read_csv("../data/8_2ipt/throughput.csv")

df["enableRts"] = df["enableRts"].astype(str).str.strip().map({
    "1": True,
    "0": False
})

df["totalSta"] = df["nDbWifi"] + df["nEbWifi"]
df["fractionDb"] = df["nDbWifi"] / df["totalSta"]

df.loc[df["nDbWifi"] == 0, "throughputBSS_DB"] = np.nan
df.loc[df["nEbWifi"] == 0, "throughputBSS_EB"] = np.nan

TOTAL_STA = 5
colors = get_colors()

fig, ax = plt.subplots(figsize=(SUBPLOT_WIDTH, SUBPLOT_HEIGHT))
d = df[df["totalSta"] == TOTAL_STA].copy()

y1 = d["throughputBSS_DB"] / d["nDbWifi"].replace(0, np.nan)
y2 = d["throughputBSS_EB"] / d["nEbWifi"].replace(0, np.nan)

current_max = np.nanmax([y1.max(), y2.max()])
y_limit = 5 * np.ceil((current_max + 1) / 5)

d_rts_on = d[d["enableRts"] == True].sort_values("fractionDb")
d_rts_off = d[d["enableRts"] == False].sort_values("fractionDb")

legend_handles = {}

# Tip: Comment out one of the plot blocks below to show only RTS/CTS ON or only RTS/CTS OFF results

# DB with RTS/CTS ON
line1, = ax.plot(
    d_rts_on["fractionDb"],
    d_rts_on["throughputBSS_DB"] / d_rts_on["nDbWifi"].replace(0, np.nan),
    color=colors["DB, RTS ON"],
    marker="o",
    zorder=3,
    label="DB, RTS ON",
    linewidth=1.5,
    markersize=6,
)
legend_handles["DB, RTS ON"] = line1

# DB with RTS/CTS OFF
line2, = ax.plot(
    d_rts_off["fractionDb"],
    d_rts_off["throughputBSS_DB"] / d_rts_off["nDbWifi"].replace(0, np.nan),
    color=colors["DB, RTS OFF"],
    marker="s",
    zorder=3,
    label="DB, RTS/CTS OFF",
    linewidth=1.5,
    markersize=6,
)
legend_handles["DB, RTS OFF"] = line2

# EB with RTS/CTS ON
line3, = ax.plot(
    d_rts_on["fractionDb"],
    d_rts_on["throughputBSS_EB"] / d_rts_on["nEbWifi"].replace(0, np.nan),
    color=colors["EB, RTS ON"],
    marker="o",
    zorder=3,
    label="EB, RTS/CTS ON",
    linewidth=1.5,
    markersize=6,
)
legend_handles["EB, RTS ON"] = line3

# EB with RTS/CTS OFF
line4, = ax.plot(
    d_rts_off["fractionDb"],
    d_rts_off["throughputBSS_EB"] / d_rts_off["nEbWifi"].replace(0, np.nan),
    color=colors["EB, RTS OFF"],
    marker="s",
    zorder=3,
    label="EB, RTS/CTS OFF",
    linewidth=1.5,
    markersize=6,
)

legend_handles["EB, RTS OFF"] = line4

ax.set_xlabel("Fraction of DB STAs")
ax.set_ylabel("Throughput per station [Mbit/s]")

ax.set_xlim(0, 1)
ax.set_ylim(0, y_limit)

ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])

# Y-axis ticks every 5, minor every 1
ax.yaxis.set_major_locator(MultipleLocator(5))
ax.yaxis.set_minor_locator(MultipleLocator(1))

ax.minorticks_off()
ax.xaxis.grid(False)
ax.yaxis.grid(True, linewidth=0.9, alpha=0.6)
    

ax.legend(
    legend_handles.values(),
    legend_handles.keys(),
    loc="lower left",
    ncol=1,
    frameon=True,
)

fig.tight_layout()

output_file = f"results/throughput_ratio_{TOTAL_STA}sta.svg"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()
