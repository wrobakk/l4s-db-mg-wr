import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from plot_config import apply_plot_style, get_cmap

apply_plot_style()

df = pd.read_csv("../data/8_15ipt/deterministic-backoff-trace.csv", header=None, names=["Time", "NodeId", "Backoff"])

node_ids = sorted(df["NodeId"].unique())
num_nodes = len(node_ids)
colors = plt.cm.viridis_r(np.linspace(0, 1, num_nodes))

for idx, node_id in enumerate(node_ids):
    df_node = df[df["NodeId"] == node_id]
    plt.plot(df_node["Time"], df_node["Backoff"], label=f"Node {node_id}", color=colors[idx])

ax = plt.gca()
ax.yaxis.set_major_locator(MultipleLocator(5))
ax.xaxis.set_major_locator(MultipleLocator(10))
plt.xlabel("Time [s]")
plt.ylabel("Backoff [slots]")
#plt.title("Deterministic Backoff - main")
#plt.legend()
ax.xaxis.grid(False)
ax.yaxis.grid(True, linewidth=0.9, alpha=0.6)

plt.xlim(0, 100)
plt.ylim(0, 80)
plt.tight_layout()
plt.savefig("results/deterministic_backoff.svg", dpi=300, bbox_inches="tight")
plt.show()
