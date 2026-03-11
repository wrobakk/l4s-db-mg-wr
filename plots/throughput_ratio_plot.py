import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()


df = pd.read_csv("../data/throughput-db-stations-ratio.csv")


df["enableRts"] = df["enableRts"].astype(str).str.strip().map({
    "True": True,
    "False": False
})


df["totalSta"] = df["nDbWifi"] + df["nEbWifi"]
df["fractionDb"] = df["nDbWifi"] / df["totalSta"]


df.loc[df["nDbWifi"] == 0, "throughputBSS_DB"] = np.nan
df.loc[df["nEbWifi"] == 0, "throughputBSS_EB"] = np.nan

totals = [5, 10, 20, 40]
colors = get_cmap(4)

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

    d_rts_on = d[d["enableRts"] == True].sort_values("fractionDb")
    d_rts_off = d[d["enableRts"] == False].sort_values("fractionDb")

    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_DB"],
        color=colors[0],
        marker="o",
        zorder=3,
        label="DB, RTS on",
    )

    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_DB"],
        color=colors[1],
        marker="s",
        zorder=3,
        label="DB, RTS off",
    )

    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_EB"],
        color=colors[2],
        marker="o",
        zorder=3,
        label="EB, RTS on",
    )

    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_EB"],
        color=colors[3],
        marker="s",
        zorder=3,
        label="EB, RTS off",
    )

    ax.set_title(f"{total} STAs")
    ax.set_xlabel("Fraction of DB STAs")
    ax.set_ylabel("Throughput [Mbit/s]")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 130)

    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])

    ax.grid(True, zorder=0)

""" fig.subplots_adjust(
    left=0.08,
    right=0.98,
    top=0.9,
    bottom=0.1,
    wspace=0.22,
    hspace=0.28,
) """


fig.suptitle("Throughput vs fraction of DB STAs for 5, 10, 20 and 40 stations, IEEE 802.11ax, MCS 11, 20 MHz, GI 800 ns, payload 1450 B, offered load 150 Mb/s per station,staggered startup (1 STA/s), warm-up 30 s after the last start, total simulation time 200 s")

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    loc='lower center',
    ncol=2,
    frameon=True,
    #bbox_to_anchor=(0.5, 0.01)
)

plt.show()