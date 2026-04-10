import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()

df = pd.read_csv("../data/7_15ipt/singlestation.csv")

df["enableRts"] = df["enableRts"].astype(str).str.strip().map({
    "True": True,
    "False": False
})

df["totalSta"] = df["nDbWifi"] + df["nEbWifi"]

# przypadek: 1 DB + (N-1) EB
single_db = df[df["nDbWifi"] == 1].copy()
single_db["ratio"] = single_db["throughputBSS_DB"] / (
    single_db["throughputBSS_EB"] / single_db["nEbWifi"]
)

# przypadek: (N-1) DB + 1 EB
single_eb = df[df["nEbWifi"] == 1].copy()
single_eb["ratio"] = single_eb["throughputBSS_EB"] / (
    single_eb["throughputBSS_DB"] / single_eb["nDbWifi"]
)

colors = get_cmap(4)

fig, ax = plt.subplots(figsize=(SUBPLOT_WIDTH, SUBPLOT_HEIGHT))

db_on = single_db[single_db["enableRts"] == True].sort_values("totalSta")
db_off = single_db[single_db["enableRts"] == False].sort_values("totalSta")
eb_on = single_eb[single_eb["enableRts"] == True].sort_values("totalSta")
eb_off = single_eb[single_eb["enableRts"] == False].sort_values("totalSta")

ax.plot(
    db_on["totalSta"], db_on["ratio"],
    marker="o", color=colors[0], label="DB RTS/CTS ON", zorder=3
)

ax.plot(
    db_off["totalSta"], db_off["ratio"],
    marker="s", color=colors[1], label="DB RTS/CTS OFF", zorder=3
)

ax.plot(
    eb_on["totalSta"], eb_on["ratio"],
    marker="o", color=colors[2], label="EB RTS/CTS ON", zorder=3
)

ax.plot(
    eb_off["totalSta"], eb_off["ratio"],
    marker="s", color=colors[3], label="EB RTS/CTS OFF", zorder=3
)

ax.set_title("Single station throughput relative to competitor average")
ax.set_xlabel("Total number of STAs")
ax.set_ylabel("Throughput ratio: single station / average competitor station")

ax.set_xticks([2, 4, 8, 16, 24])
ax.set_xlim(1.5, 24.5)

current_max = np.nanmax([
    single_db["ratio"].max(),
    single_eb["ratio"].max()
])
y_limit = 0.2 * np.ceil((current_max + 0.1) / 0.2)
ax.set_ylim(0, y_limit)

ax.yaxis.set_major_locator(MultipleLocator(0.2))

ax.grid(True, which="major", alpha=1, zorder=0, axis='y')
ax.legend(loc="best", frameon=True)

fig.suptitle(
    "\n$\\mathbf{Deterministic \\: backoff = 7 + 1.5*ipt}$"
)

plt.tight_layout()
plt.savefig("minority_station_relative_throughput.png", dpi=300, bbox_inches="tight")
plt.show()