import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from plot_config import apply_plot_style, get_colors, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

df = pd.read_csv("../data/9_15ipt/throughput.csv")

df["enableRts"] = df["enableRts"].astype(str).str.strip().map({
    "True": True,
    "False": False
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

line1, = ax.plot(
    d_rts_on["fractionDb"],
    d_rts_on["throughputBSS_DB"] / d_rts_on["nDbWifi"].replace(0, np.nan),
    color=colors["DB, RTS ON"],
    marker="o",
    zorder=3,
    label="DB, RTS/CTS ON",
    linewidth=1.5,
    markersize=6,
)
legend_handles["DB, RTS ON"] = line1

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
ax.yaxis.grid(True)

ax.legend(
    legend_handles.values(),
    legend_handles.keys(),
    loc="lower left",
    ncol=1,
    frameon=True,
)

fig.suptitle(
    "Throughput per station vs fraction of DB STAs for "
    f"{TOTAL_STA} STA\n"
    "staggered startup (1 STA/s), warm-up 30 s after the last start, \ntotal simulation time 200 s, \n"
    "\n$\\mathbf{Deterministic \\: backoff = 8 + 1.5*ipt}$"
)

fig.tight_layout(rect=[0, 0.08, 1, 0.93])

output_file = f"throughput_ratio_{TOTAL_STA}sta.svg"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()
