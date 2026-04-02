import subprocess
import csv
import re

NS3_DIR = "."
SIMULATION = "scratch/ac-be-main"

WIFI_PAIRS = [
    (0, 10),
    (2, 8),
    (4, 6),
    (6, 4),
    (8, 2),
    (10, 0),
    (0, 20),
    (4, 16),
    (8, 12),
    (12, 8),
    (16, 4),
    (20, 0),
    (0, 40),
    (8, 32),
    (16, 24),
    (24, 16),
    (32, 8),
    (40, 0),
]

RTS_VALUES = [True, False]
SIMULATION_TIME = 200


CSV_FILE = "summaryallsta.csv"


def build_command(n_db, n_eb, rts):
    rts_str = "true" if rts else "false"

    return (
        f'./ns3 run "{SIMULATION} '
        f'--nDbWifi={n_db} '
        f'--nEbWifi={n_eb} '
        f'--enableRts={rts_str} '
        f'--simulationTime={SIMULATION_TIME}"'
    )


def extract_throughputs(output_text):
    db_match = re.search(r"Throughput BSS_DB:\s*([0-9.+-eE]+)", output_text)
    eb_match = re.search(r"Throughput BSS_EB:\s*([0-9.+-eE]+)", output_text)

    thr_db = float(db_match.group(1)) if db_match else ""
    thr_eb = float(eb_match.group(1)) if eb_match else ""

    return thr_db, thr_eb


def main():
    rows = []

    for n_db, n_eb in WIFI_PAIRS:
        for rts in RTS_VALUES:
            cmd = build_command(n_db, n_eb, rts)
            print(f"\nUruchamiam: {cmd}")

            result = subprocess.run(
                cmd,
                cwd=NS3_DIR,
                shell=True,
                capture_output=True,
                text=True
            )

            full_output = result.stdout + "\n" + result.stderr
            thr_db, thr_eb = extract_throughputs(full_output)

            if thr_db == "" or thr_eb == "":
                print("Cant't read throughput.")
                print(full_output)

            rows.append({
                "nDbWifi": n_db,
                "nEbWifi": n_eb,
                "simulationTime": SIMULATION_TIME,
                "enableRts": rts,
                "throughputBSS_DB": thr_db,
                "throughputBSS_EB": thr_eb
            })

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "nDbWifi",
                "nEbWifi",
                "simulationTime",
                "enableRts",
                "throughputBSS_DB",
                "throughputBSS_EB"
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults are in: {CSV_FILE}")


if __name__ == "__main__":
    main()