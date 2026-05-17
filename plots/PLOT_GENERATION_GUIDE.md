# Figure Generation Guide

This guide explains how to generate figures from the dataset using the provided plotting scripts.

## Overview

There are 4 main plotting scripts available:

1. **throughput_vs_sta_fraction.py** - 2x2 subplot comparison of per-station throughput
2. **single_count_throughput_vs_fraction.py** - Single plot for fixed STA count
3. **ccdf_txop_latency.py** - CCDF plots with multiple DB/EB configurations
4. **ccdf_single_config.py** - CCDF plot for a single DB/EB configuration

---

## 1. Throughput vs STA Fraction (Multi-config comparison)

**File:** `throughput_vs_sta_fraction.py`

**Description:** Generates a 2x2 subplot visualization comparing per-station throughput across 4 different total STA counts (5, 10, 20, 40). Each subplot shows how throughput varies with DB/EB station fraction for both RTS/CTS ON and OFF.

**Usage:**

1. Edit the data source path (near line 20):
   ```python
   df = pd.read_csv("../data/7_15ipt/throughput.csv")  # Change this path
   ```

2. (Optional) To show only RTS/CTS ON or OFF results, comment out the corresponding plot blocks around lines 60-90:
   ```python
   # DB with RTS/CTS ON
   ax.plot(...)
   
   # DB with RTS/CTS OFF - comment this block if you only want RTS ON
   # ax.plot(...)
   ```

3. Run the script:
   ```bash
   python throughput_vs_sta_fraction.py
   ```

4. Output: `results/throughput[X]_[Y]ipt_ratio.svg`

---

## 2. Single Count Throughput Analysis

**File:** `single_count_throughput_vs_fraction.py`

**Description:** Generates a single plot for a fixed STA count. Useful for zoomed-in analysis of specific scenario (e.g., only 5 STAs).

**Usage:**

1. Edit the data source path (near line 20):
   ```python
   df = pd.read_csv("../data/8_15ipt/throughput.csv")  # Change this path
   ```

2. Change the STA count to analyze (near line 25):
   ```python
   TOTAL_STA = 5  # Change to desired count (5, 10, 20, or 40)
   ```

3. (Optional) Comment/uncomment plot blocks to show/hide RTS/CTS results (around lines 35-75)

4. Run the script:
   ```bash
   python single_count_throughput_vs_fraction.py
   ```

5. Output: `results/single_count_[TOTAL_STA]_throughput.svg`

---

## 3. CCDF TXOP Latency (Multiple configurations)

**File:** `ccdf_txop_latency.py`

**Description:** Generates CCDF (Cumulative Distribution Function) plots showing TXOP latency/delay distribution. The 2x2 subplot compares different DB/EB configurations for a specific STA count.

**File Naming Convention:**
```
txop-trace-[DB|EB]-[nDB]-[nEB]-[RTS].csv
  - [DB|EB]: Station type (DB or EB stations data)
  - [nDB]: Total number of DB stations in simulation
  - [nEB]: Total number of EB stations in simulation
  - [RTS]: RTS/CTS mode (1=ON, 0=OFF)
  
Example: txop-trace-db-2-3-1.csv = DB station delays from sim with 2 DB + 3 EB stations, RTS/CTS ON
```

**Usage:**

1. Edit the data source path (near line 22):
   ```python
   DATA_DIR = Path("../data/8_15ipt/txop_08_04")  # Change this path
   ```

2. Change the STA count and configurations (near lines 25-28):
   ```python
   TOTAL_STA = 5
   configs = [(1, 4), (2, 3), (3, 2), (4, 1)]  # 5 STAs - change for 10/20/40 STAs
   
   # For 10 STAs:
   # configs = [(0, 10), (2, 8), (4, 6), (6, 4), (8, 2), (10, 0)]
   ```

3. Adjust X-axis limit if needed (near line 27):
   ```python
   X_LIM = (0, 2000)  # Change based on expected delay range
   ```

4. (Optional) Uncomment RTS/CTS ON lines in build_files() function to include those results

5. Run the script:
   ```bash
   python ccdf_txop_latency.py
   ```

6. Output: `results/ccdf_[TOTAL_STA]sta_all_ratios.svg`

---

## 4. CCDF Single Configuration

**File:** `ccdf_single_config.py`

**Description:** Generates a single CCDF plot for one specific DB/EB configuration. Useful for detailed analysis of a particular scenario.

**Usage:**

1. Edit the data source path (near line 35):
   ```python
   DATA_DIR = Path("../data/8_15ipt/txop_08_04")  # Change this path
   ```

2. Set the station counts to analyze (near lines 43-44):
   ```python
   N_DB = 0    # Number of DB stations
   N_EB = 5    # Number of EB stations
   ```

3. Choose which files to plot by uncommenting/commenting lines in the FILES list (near lines 46-51):
   ```python
   FILES = [
       # Uncomment to include DB RTS/CTS ON
       #("txop-trace-db-5-0-1.csv", "DB, RTS ON"),
       ("txop-trace-db-5-0-0.csv", "DB, RTS OFF"),  # Active
       # Uncomment to include EB RTS/CTS ON and OFF
       #("txop-trace-eb-5-0-1.csv", "EB, RTS ON"),
       #("txop-trace-eb-5-0-0.csv", "EB, RTS OFF"),
   ]
   ```
   Remember: Last digit in filename = 1 (RTS ON), 0 (RTS OFF)

4. Adjust X-axis limit if needed (near line 41):
   ```python
   X_LIM = (0, 2000)  # Change based on expected delay range
   ```

5. Run the script:
   ```bash
   python ccdf_single_config.py
   ```

6. Output: `results/ccdf_nDb[N_DB]_nEb[N_EB].svg`

---

## General Notes

- All scripts output figures to the `results/` directory
- Ensure the data CSV files exist at the specified paths
- The `plot_config.py` module must be in the same directory (contains styling and color definitions)
- Edit paths and parameters directly in the script files
- All figures are saved as SVG format (scalable vector graphics)

## Dataset Structure

Expected data directory structure:
```
data/
  [X]_[Y]ipt/
    throughput.csv              # For throughput plots
    txop_[XX]_[YY]/
      txop-trace-*.csv          # For CCDF plots
```

Example:
```
data/8_15ipt/
  throughput.csv
  txop_08_04/
    txop-trace-db-2-3-0.csv
    txop-trace-db-2-3-1.csv
    txop-trace-eb-2-3-0.csv
    txop-trace-eb-2-3-1.csv
    ... (more configurations)
```

