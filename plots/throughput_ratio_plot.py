import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

df = pd.read_csv("../data/before_patches/6_15ipt/throughput.csv")


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

    # Obliczanie throughput per station dla wszystkich serii, aby znaleźć max_val
    y1 = d["throughputBSS_DB"] / d["nDbWifi"].replace(0, np.nan)
    y2 = d["throughputBSS_EB"] / d["nEbWifi"].replace(0, np.nan)
    
    # Wyznaczenie maksymalnej wartości w aktualnym subplocie (ignorując NaN)
    current_max = np.nanmax([y1.max(), y2.max()])
    
    # Zaokrąglenie w górę do najbliższej wielokrotności 5
    # Dodajemy mały margines (np. +1), aby punkty nie dotykały samej góry ramki
    y_limit = 5 * np.ceil((current_max + 1) / 5)
    
    d_rts_on = d[d["enableRts"] == True].sort_values("fractionDb")
    d_rts_off = d[d["enableRts"] == False].sort_values("fractionDb")

    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_DB"] / d_rts_on["nDbWifi"].replace(0, np.nan),
        color=colors[0], marker="o", zorder=3, label="DB, RTS/CTS ON",
    )

    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_DB"] / d_rts_off["nDbWifi"].replace(0, np.nan),
        color=colors[1], marker="s", zorder=3, label="DB, RTS/CTS OFF",
    )

    ax.plot(
        d_rts_on["fractionDb"],
        d_rts_on["throughputBSS_EB"] / d_rts_on["nEbWifi"].replace(0, np.nan),
        color=colors[2], marker="o", zorder=3, label="EB, RTS/CTS ON",
    )

    ax.plot(
        d_rts_off["fractionDb"],
        d_rts_off["throughputBSS_EB"] / d_rts_off["nEbWifi"].replace(0, np.nan),
        color=colors[3], marker="s", zorder=3, label="EB, RTS/CTS OFF",
    )

    ax.set_title(f"{total} STAs")
    ax.set_xlabel("Fraction of DB STAs")
    ax.set_ylabel("Throughput per station [Mbit/s]")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, y_limit) # Ustawienie wyliczonego limitu

    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])
    
    # Ustawienie ticków co 5
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    
    ax.grid(True, which="major", alpha=1, zorder=0)
    ax.grid(True, which="minor", alpha=0.3, zorder=0)
    
    if i == 0:
        ax.legend(loc="lower left", ncol=1, frameon=True)
    else:
        ax.legend(loc="best", ncol=1, frameon=True)


fig.suptitle("Throughput per station vs fraction of DB STAs for 5, 10, 20 and 40 stations, staggered startup (1 STA/s), warm-up 30 s after the last start, total simulation time 200 s\n"
             "\n$\\mathbf{Deterministic \\: backoff = 6 + 1.5*ipt}$")

handles, labels = axes[0].get_legend_handles_labels()
"""fig.legend(
    handles,
    labels,
    loc='lower center',
    ncol=2,
    frameon=True,
    #bbox_to_anchor=(0.5, 0.01)
)"""
plt.savefig("throughput_ratio.png")
plt.show()