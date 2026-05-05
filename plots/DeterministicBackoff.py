import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

df = pd.read_csv("deterministic-backoff-trace.csv", header=None, names=["Time", "NodeId", "Backoff"])

for node_id in df["NodeId"].unique():
    df_node = df[df["NodeId"] == node_id]
    plt.plot(df_node["Time"], df_node["Backoff"], label=f"Node {node_id}")

ax = plt.gca()
ax.yaxis.set_major_locator(MultipleLocator(1))
ax.xaxis.set_major_locator(MultipleLocator(10))
plt.xlabel("Time [s]")
plt.ylabel("Backoff [slots]")
plt.title("Deterministic Backoff - main")
plt.legend()
plt.grid(True)

#plt.xlim(0, 320)
#plt.ylim(0, 40)
plt.show()
