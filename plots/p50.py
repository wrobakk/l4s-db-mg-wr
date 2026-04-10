import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path("../data/7_15ipt/txop_08_04")
TOTAL_STA = 5
GAP_SECONDS = 1
WARMUP_SECONDS = 30
X_UNIT = "ms"

configs = [(0, 5), (1, 4), (2, 3), (3, 2), (4, 1), (5, 0)]   # 5 STAs
#configs = [(0, 10), (2, 8), (4, 6), (6, 4), (8, 2), (10, 0)]  # 10 STAs
#configs = [(0, 20), (4, 16), (8, 12), (12, 8), (16, 4), (20, 0)]  # 20 STAs
#configs = [(0, 40), (8, 32), (16, 24), (24, 16), (32, 8), (40, 0)]  # 40 STAs


def get_unit_divisor(unit):
    if unit == "ns":
        return 1.0
    if unit == "us":
        return 1e3
    if unit == "ms":
        return 1e6
    if unit == "s":
        return 1e9
    raise ValueError(f"Unsupported unit: {unit}")


def compute_cut_time_ns(n_db, n_eb, gap_s, warmup_s):
    n_stations = n_db + n_eb
    cut_time_s = n_stations * gap_s + warmup_s
    return cut_time_s * 1e9


def load_delays(csv_file, n_db, n_eb, gap_s, warmup_s, unit="ms"):
    cols = ["time_s", "node_id", "start_ns", "duration_ns", "success"]
    df = pd.read_csv(csv_file, names=cols)

    # 0 == successful TXOP
    df = df[df["success"] == 0].copy()

    cut_time_ns = compute_cut_time_ns(n_db, n_eb, gap_s, warmup_s)
    df = df[df["start_ns"] >= cut_time_ns].copy()

    if df.empty:
        return np.array([])

    df["end_ns"] = df["start_ns"] + df["duration_ns"]
    df = df.sort_values(["node_id", "start_ns"]).copy()
    df["prev_end_ns"] = df.groupby("node_id")["end_ns"].shift(1)
    df["delay_ns"] = df["start_ns"] - df["prev_end_ns"]

    df = df.dropna(subset=["prev_end_ns"]).copy()
    df = df[df["delay_ns"] >= 0].copy()

    if df.empty:
        return np.array([])

    return df["delay_ns"].to_numpy() / get_unit_divisor(unit)


def compute_p90(delays):
    if len(delays) == 0:
        return np.nan
    return np.percentile(delays, 90)


def build_files(n_db, n_eb):
    files = []

    if n_db > 0:
        files.append((f"txop-trace-db-{n_db}-{n_eb}-1.csv", "DB", True))
        files.append((f"txop-trace-db-{n_db}-{n_eb}-0.csv", "DB", False))

    if n_eb > 0:
        files.append((f"txop-trace-eb-{n_db}-{n_eb}-1.csv", "EB", True))
        files.append((f"txop-trace-eb-{n_db}-{n_eb}-0.csv", "EB", False))

    return files


rows = []

for n_db, n_eb in configs:
    files = build_files(n_db, n_eb)

    for filename, access_type, enable_rts in files:
        path = DATA_DIR / filename

        if not path.exists():
            print(f"No file: {path}")
            continue

        delays = load_delays(
            csv_file=path,
            n_db=n_db,
            n_eb=n_eb,
            gap_s=GAP_SECONDS,
            warmup_s=WARMUP_SECONDS,
            unit=X_UNIT,
        )

        p90 = compute_p90(delays)

        rows.append({
            "nDbWifi": n_db,
            "nEbWifi": n_eb,
            "simulationTime": 200,
            "enableRts": enable_rts,
            "accessType": access_type,
            f"p90_{X_UNIT}": p90,
        })

results_df = pd.DataFrame(rows)

output_csv = f"p90_channel_access_delay_{TOTAL_STA}sta.csv"
results_df.to_csv(output_csv, index=False)

print(results_df)
print(f"\nSaved to: {output_csv}")