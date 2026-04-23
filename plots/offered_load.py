import pandas as pd
import matplotlib.pyplot as plt

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

CSV_FILE = "../data/8_15ipt/offered_load_sweep_8_15_ipt.csv"

configs = [(0, 5), (1, 4), (2, 3), (3, 2), (4, 1), (5, 0)]  # 5 STAs

colors = {
    "DB, RTS ON": get_cmap(4)[0],
    "DB, RTS OFF": get_cmap(4)[1],
    "EB, RTS ON": get_cmap(4)[2],
    "EB, RTS OFF": get_cmap(4)[3],
}

df = pd.read_csv(CSV_FILE)

df["enableRts"] = (
    df["enableRts"]
    .astype(str)
    .str.strip()
    .map({"True": True, "False": False})
)

fig, axes = plt.subplots(
    2, 3,
    figsize=(3 * SUBPLOT_WIDTH, 2.2 * SUBPLOT_HEIGHT),
)
axes = axes.flatten()

for ax, (n_db, n_eb) in zip(axes, configs):
    subset = df[
        (df["nDbWifi"] == n_db) &
        (df["nEbWifi"] == n_eb)
    ].copy()

    subset = subset.sort_values("offeredRate_Mbps")

    subplot_handles = {}

    # DB per-station throughput
    if n_db > 0:
        for rts, label, marker in [
            (True, "DB, RTS ON", "o"),
            (False, "DB, RTS OFF", "s"),
        ]:
            data = subset[subset["enableRts"] == rts].copy()
            if data.empty:
                continue

            data["throughput_per_station"] = data["throughputBSS_DB"] / n_db

            line, = ax.plot(
                data["offeredRate_Mbps"],
                data["throughput_per_station"],
                color=colors[label],
                marker=marker,
                zorder=3,
                label=label,
            )
            subplot_handles[label] = line

    # EB per-station throughput
    if n_eb > 0:
        for rts, label, marker in [
            (True, "EB, RTS ON", "o"),
            (False, "EB, RTS OFF", "s"),
        ]:
            data = subset[subset["enableRts"] == rts].copy()
            if data.empty:
                continue

            data["throughput_per_station"] = data["throughputBSS_EB"] / n_eb

            line, = ax.plot(
                data["offeredRate_Mbps"],
                data["throughput_per_station"],
                color=colors[label],
                marker=marker,
                zorder=3,
                label=label,
            )
            subplot_handles[label] = line

    ax.set_title(f"{n_db} DB, {n_eb} EB")
    ax.set_xlim(0, 29)
    ax.set_ylim(bottom=0)
    ax.set_xticks(range(0, 30, 3))
    ax.grid(True, zorder=0)
    ax.set_xlabel("Offered load per station [Mbps]")
    ax.set_ylabel("Throughput per station [Mbps]")

    if subplot_handles:
        ax.legend(
            subplot_handles.values(),
            subplot_handles.keys(),
            loc="best",
            ncol=1,
            frameon=True,
        )

fig.suptitle(
    "Per-station throughput vs offered load for 5 stations, total simulation time 200 s\n"
    "\n$\\mathbf{Deterministic \\: backoff = 8 + 1.5*ipt}$"
)

fig.tight_layout(rect=[0, 0.0, 1, 0.95])

output_file = "results/throughput_per_station_vs_offered_load_5sta_all_ratios.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()