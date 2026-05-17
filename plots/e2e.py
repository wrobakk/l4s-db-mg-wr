import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from plot_config import apply_plot_style, get_colors, SUBPLOT_WIDTH, SUBPLOT_HEIGHT

apply_plot_style()


# =========================
# CONFIG
# =========================

DATA_DIR = Path("../data/8_15ipt/txrx")
OUTPUT_DIR = Path("results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "p99_e2e_delay_5sta_all_ratios.svg"

CONFIGS = [
    (0, 5),
    (1, 4),
    (2, 3),
    (3, 2),
    (4, 1),
    (5, 0),
]

RTS_VALUES = [0]

# offered load per station [bps]
OFFERED_RATES = [
    1_000_000,
    5_000_000,
    9_000_000,
    13_000_000,
    17_000_000,
    21_000_000,
    25_000_000,
    29_000_000,
]

# zgodnie z ustaleniem:
# staggered startup + warm-up => odcinamy wszystko przed 35 s
CUT_TIME_SECONDS = 35

X_UNIT = "Mbit/s"
Y_UNIT = "ms"

USE_LOG_Y = False

colors = get_colors()


# =========================
# HELPERS
# =========================

def build_txrx_filename(n_db, n_eb, rts, offered_rate):
    """
    Obecny format nazw plików:
    txrx.csv-db0-eb5-rts1-rate1000000.csv
    """
    return f"txrx.csv-db{n_db}-eb{n_eb}-rts{rts}-rate{offered_rate}.csv"


def load_txrx(csv_file):
    """
    Plik bez nagłówka.
    Format:
    time,event,group,nodeId,packetUid

    Przykład:
    35.002,TX,DB,1,500
    35.006,RX,DB,0,500
    """
    cols = ["time", "event", "group", "nodeId", "packetUid"]
    df = pd.read_csv(csv_file, names=cols, header=None)

    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df["nodeId"] = pd.to_numeric(df["nodeId"], errors="coerce")
    df["packetUid"] = pd.to_numeric(df["packetUid"], errors="coerce")

    df = df.dropna(subset=["time", "nodeId", "packetUid"]).copy()

    df["nodeId"] = df["nodeId"].astype(int)
    df["packetUid"] = df["packetUid"].astype(int)
    df["event"] = df["event"].astype(str).str.strip()
    df["group"] = df["group"].astype(str).str.strip()

    return df


def compute_group_delays_ms(df, group, cut_time_s):
    """
    Liczy MAC end-to-end delay:
    delay = pierwszy RX - pierwszy TX dla tego samego packetUid.

    Liczone osobno dla DB i EB.

    UWAGA:
    - bierzemy tylko próbki po cut_time_s (warm-up)
    - pakiety bez pary TX/RX są ignorowane
      (bo nie da się policzyć delay = RX - TX)
    """
    df_group = df[df["group"] == group].copy()

    if df_group.empty:
        return np.array([])

    tx = df_group[(df_group["event"] == "TX") & (df_group["time"] >= cut_time_s)].copy()
    rx = df_group[(df_group["event"] == "RX") & (df_group["time"] >= cut_time_s)].copy()

    if tx.empty or rx.empty:
        return np.array([])

    # pierwszy TX i pierwszy RX dla danego packetUid
    tx_first = tx.groupby("packetUid")["time"].min()
    rx_first = rx.groupby("packetUid")["time"].min()

    # zostają tylko pakiety, które wystąpiły zarówno w TX jak i RX
    common_uids = tx_first.index.intersection(rx_first.index)

    if len(common_uids) == 0:
        return np.array([])

    delays_s = rx_first.loc[common_uids] - tx_first.loc[common_uids]
    delays_s = delays_s[delays_s >= 0]

    if delays_s.empty:
        return np.array([])

    return delays_s.to_numpy() * 1000.0


def compute_p99(values):
    if len(values) == 0:
        return np.nan
    return np.percentile(values, 99)


def nice_upper_limit(values, fallback=2.0):
    """
    Zaokrągla górny limit osi Y do 'ładnej' wartości.
    """
    finite_vals = [v for v in values if np.isfinite(v)]
    if not finite_vals:
        return fallback

    vmax = max(finite_vals)
    if vmax <= 0:
        return fallback

    raw = 1.05 * vmax
    exponent = math.floor(math.log10(raw))
    fraction = raw / (10 ** exponent)

    if fraction <= 1:
        nice = 1
    elif fraction <= 2:
        nice = 2
    elif fraction <= 5:
        nice = 5
    else:
        nice = 10

    return nice * (10 ** exponent)


# =========================
# LOAD DATA
# =========================

rows = []
missing_files = []

for n_db, n_eb in CONFIGS:
    for rts in RTS_VALUES:
        for offered_rate in OFFERED_RATES:
            filename = build_txrx_filename(n_db, n_eb, rts, offered_rate)
            path = DATA_DIR / filename

            if not path.exists():
                missing_files.append(filename)
                continue

            df = load_txrx(path)

            for group in ["DB", "EB"]:
                delays_ms = compute_group_delays_ms(
                    df=df,
                    group=group,
                    cut_time_s=CUT_TIME_SECONDS,
                )

                if len(delays_ms) == 0:
                    continue

                rows.append({
                    "nDbWifi": n_db,
                    "nEbWifi": n_eb,
                    "enableRts": rts,
                    "group": group,
                    "offeredRate_Mbps": offered_rate / 1e6,
                    "p99Delay_ms": compute_p99(delays_ms),
                })

plot_df = pd.DataFrame(rows)

if plot_df.empty:
    raise RuntimeError("No data loaded. Check DATA_DIR and file names.")

if missing_files:
    print(f"Missing files: {len(missing_files)}")
    for name in missing_files[:10]:
        print(f"  {name}")
    if len(missing_files) > 10:
        print("  ...")


# =========================
# PLOT
# =========================

fig, axes = plt.subplots(
    2,
    3,
    figsize=(3 * SUBPLOT_WIDTH, 2 * SUBPLOT_HEIGHT),
    sharex=True,
    sharey=True,
)
axes = axes.flatten()

style_map = {
    ("DB", 1): {
        "label": "DB, RTS ON",
        "color": colors["DB, RTS ON"],
        "linestyle": "-",
        "marker": "o",
    },
    ("DB", 0): {
        "label": "DB, RTS OFF",
        "color": colors["DB, RTS OFF"],
        "linestyle": "-",
        "marker": "s",
    },
    ("EB", 1): {
        "label": "EB, RTS ON",
        "color": colors["EB, RTS ON"],
        "linestyle": "-",
        "marker": "o",
    },
    ("EB", 0): {
        "label": "EB, RTS OFF",
        "color": colors["EB, RTS OFF"],
        "linestyle": "-",
        "marker": "s",
    },
}
#y_max = np.ceil((1.1 * plot_df["p99Delay_ms"].max()) / 100) * 100

x_ticks = [0] + [rate / 1e6 for rate in OFFERED_RATES]
x_max = max(x_ticks)

for ax, (n_db, n_eb) in zip(axes, CONFIGS):
    scenario_df = plot_df[
        (plot_df["nDbWifi"] == n_db) &
        (plot_df["nEbWifi"] == n_eb)
    ].copy()

    for group in ["DB", "EB"]:
        for rts in RTS_VALUES:
            line_df = scenario_df[
                (scenario_df["group"] == group) &
                (scenario_df["enableRts"] == rts)
            ].copy()

            if line_df.empty:
                continue

            line_df = line_df.sort_values("offeredRate_Mbps")
            style = style_map[(group, rts)]

            ax.plot(
                line_df["offeredRate_Mbps"],
                line_df["p99Delay_ms"],
                color=style["color"],
                linestyle=style["linestyle"],
                marker=style["marker"],
                linewidth=1.5,
                markersize=4,
                zorder=3,
                label=style["label"],
            )

    ax.set_title(f"{n_db} DB, {n_eb} EB")

    # opisy osi na KAŻDYM subplocie
    ax.set_xlabel(f"Offered load per station [{X_UNIT}]")
    ax.set_ylabel(f"End-to-End delay [{Y_UNIT}]")

    # skala / ticki na KAŻDYM subplocie
    ax.set_xticks(x_ticks)
    ax.tick_params(axis="x", labelbottom=True)
    ax.tick_params(axis="y", labelleft=True)

    # każda oś zaczyna się od 0
    ax.set_xlim(left=0, right=x_max)

    if USE_LOG_Y:
        ax.set_yscale("log")
    else:
        ax.set_ylim(bottom=0, top=1200)

    ax.minorticks_off()
    ax.grid(True, which="major", axis="y", zorder=0)

    # legenda na KAŻDYM subplocie, jedna kolumna
    ax.legend(
        loc=2,
        ncol=1,
        frameon=True,
    )

# fig.suptitle(
#     "P99 of MAC end-to-end delay for 5 stations"
# )

fig.tight_layout()

fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.show()