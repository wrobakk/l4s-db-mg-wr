from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from plot_config import apply_plot_style, get_cmap, SUBPLOT_WIDTH, SUBPLOT_HEIGHT


apply_plot_style()

df = pd.read_csv("../data/10_15ipt/singlestation.csv")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(exist_ok=True)

df["enableRts"] = df["enableRts"].astype(str).str.strip().map({
    "True": True,
    "False": False
})

df["totalSta"] = df["nDbWifi"] + df["nEbWifi"]

# throughput pojedynczej stacji DB: przypadki 1 DB + (N-1) EB
single_db = df[df["nDbWifi"] == 1].copy()
single_db["singleStaThroughput"] = single_db["throughputBSS_DB"]

# throughput pojedynczej stacji EB: przypadki (N-1) DB + 1 EB
single_eb = df[df["nEbWifi"] == 1].copy()
single_eb["singleStaThroughput"] = single_eb["throughputBSS_EB"]

colors = get_cmap(4)

fig, ax = plt.subplots(figsize=(SUBPLOT_WIDTH, SUBPLOT_HEIGHT))

db_on = single_db[single_db["enableRts"] == True].sort_values("totalSta")
db_off = single_db[single_db["enableRts"] == False].sort_values("totalSta")
eb_on = single_eb[single_eb["enableRts"] == True].sort_values("totalSta")
eb_off = single_eb[single_eb["enableRts"] == False].sort_values("totalSta")

ax.plot(
    db_on["totalSta"], db_on["singleStaThroughput"],
    marker="o", color=colors[0], label="Single DB, RTS/CTS ON", zorder=3
)

ax.plot(
    db_off["totalSta"], db_off["singleStaThroughput"],
    marker="s", color=colors[1], label="Single DB, RTS/CTS OFF", zorder=3
)

ax.plot(
    eb_on["totalSta"], eb_on["singleStaThroughput"],
    marker="o", color=colors[2], label="Single EB, RTS/CTS ON", zorder=3
)

ax.plot(
    eb_off["totalSta"], eb_off["singleStaThroughput"],
    marker="s", color=colors[3], label="Single EB, RTS/CTS OFF", zorder=3
)

ax.set_title("Single station throughput vs total number of STAs")
ax.set_xlabel("Total number of STAs")
ax.set_ylabel("Single station throughput [Mbit/s]")

ax.set_xticks([2, 4, 8, 16, 24])
ax.set_xlim(1.5, 24.5)

current_max = np.nanmax([
    single_db["singleStaThroughput"].max(),
    single_eb["singleStaThroughput"].max()
])

ax.set_ylim(0, 80)

ax.yaxis.set_major_locator(MultipleLocator(10))
ax.yaxis.set_minor_locator(MultipleLocator(1))

ax.minorticks_off()
ax.xaxis.grid(False)
ax.yaxis.grid(True, linewidth=0.9, alpha=0.6)
ax.legend(loc="best", frameon=True)

fig.suptitle(
    "$\\mathbf{Deterministic \\: backoff = 10 + 1.5*ipt}$"
)

plt.tight_layout()
OUTPUT_FILE = OUTPUT_DIR / "single_miniority_throughput.svg"
fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.show()