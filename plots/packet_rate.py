
import pandas as pd
import numpy as np

CSV_FILE = "../data/8_15ipt/offered_load_sweep_8_15_ipt.csv"
OUT_FILE = "../data/8_15ipt/offered_load_sweep_8_15_ipt_with_pps.csv"

PAYLOAD_BYTES = 1450
BITS_PER_PACKET = PAYLOAD_BYTES * 8

df = pd.read_csv(CSV_FILE)

# per-station throughput [Mbps]
df["throughputDbPerSta_Mbps"] = np.where(
    df["nDbWifi"] > 0,
    df["throughputBSS_DB"] / df["nDbWifi"],
    np.nan
)

df["throughputEbPerSta_Mbps"] = np.where(
    df["nEbWifi"] > 0,
    df["throughputBSS_EB"] / df["nEbWifi"],
    np.nan
)

# achieved packet rate [pps]
df["ppsDbPerSta"] = df["throughputDbPerSta_Mbps"] * 1e6 / BITS_PER_PACKET
df["ppsEbPerSta"] = df["throughputEbPerSta_Mbps"] * 1e6 / BITS_PER_PACKET

# average interval between packets [us]
df["intervalDb_us"] = 1e6 / df["ppsDbPerSta"]
df["intervalEb_us"] = 1e6 / df["ppsEbPerSta"]

# opcjonalnie ładne zaokrąglenie
df["throughputDbPerSta_Mbps"] = df["throughputDbPerSta_Mbps"].round(3)
df["throughputEbPerSta_Mbps"] = df["throughputEbPerSta_Mbps"].round(3)
df["ppsDbPerSta"] = df["ppsDbPerSta"].round(1)
df["ppsEbPerSta"] = df["ppsEbPerSta"].round(1)
df["intervalDb_us"] = df["intervalDb_us"].round(1)
df["intervalEb_us"] = df["intervalEb_us"].round(1)

df.to_csv(OUT_FILE, index=False)
print(f"Saved: {OUT_FILE}")

print(df[[
    "nDbWifi", "nEbWifi", "enableRts", "offeredRate_Mbps",
    "throughputDbPerSta_Mbps", "throughputEbPerSta_Mbps",
    "ppsDbPerSta", "ppsEbPerSta",
    "intervalDb_us", "intervalEb_us"
]].head(20))