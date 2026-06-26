# Deterministic Backoff Simulation and Result Processing

This repository contains the simulation scenario, collected datasets, and data-processing scripts used in the master's thesis concerning the evaluation of Deterministic Backoff in IEEE 802.11ax networks.

The study focuses on the coexistence of stations using Deterministic Backoff (DB) and the standard Exponential Backoff (EB). The evaluated metrics include per-station throughput and channel access delay for different numbers and proportions of DB and EB stations.

## Repository Scope

The repository contains:

* the ns-3 simulation scenario used to collect the results,
* CSV files containing the processed throughput results,
* TXOP trace files used to calculate channel access delay,
* Python scripts used to process the collected data,
* Python scripts used to generate the figures presented in the thesis.

The implementation of the DB mechanism is not included in this repository. It is maintained in a private CableLabs fork of ns-3 and is not currently publicly available.

As a result, the provided simulation scenario requires a compatible ns-3 version containing the DB implementation. However, the included datasets and Python scripts can be used independently to reproduce the figures presented in the thesis.

## Repository Structure

```text
.
├── data/
├── scripts/
└── results/
    └── ac-be-main.cc
```

The exact directory names may depend on the simulation configuration represented by a particular dataset.

## Simulation Scenario

### `ac-be-main.cc`

This file contains the ns-3 scenario used to evaluate the coexistence of DB and EB stations.

The scenario consists of two IEEE 802.11ax basic service sets operating on the same wireless channel:

* one BSS contains stations using Deterministic Backoff,
* the other BSS contains stations using Exponential Backoff.

The number of DB and EB stations can be configured separately. This allows different proportions of both channel access mechanisms to be evaluated while keeping the total number of stations fixed.

All stations generate uplink UDP traffic towards their corresponding access point. Station transmissions begin at different times according to the configured start interval. Throughput measurements start after all stations have begun transmitting and the configured warm-up period has elapsed.

The scenario records:

* aggregate throughput of DB stations,
* aggregate throughput of EB stations,
* TXOP start times,
* TXOP durations,
* failed TXOP attempts.

### Simulation Parameters

The main command-line parameters supported by the scenario are:

| Parameter        | Description                                  | Default |
| ---------------- | -------------------------------------------- | ------: |
| `nDbWifi`        | Number of DB stations                        |     `1` |
| `nEbWifi`        | Number of EB stations                        |     `1` |
| `channelWidth`   | Channel width in MHz                         |    `20` |
| `gi`             | Guard interval in nanoseconds                |   `800` |
| `enableRts`      | Enables or disables RTS/CTS                  |  `true` |
| `payloadSize`    | UDP payload size in bytes                    |  `1450` |
| `simulationTime` | Total simulation duration in seconds         |    `30` |
| `baseStart`      | Start time of the first station              |     `0` |
| `gap`            | Time between consecutive station starts      |     `1` |
| `warmup`         | Warm-up period after the last station starts |    `30` |
| `pcap`           | Enables PCAP generation                      | `false` |

The scenario uses IEEE 802.11ax in the 5 GHz band and the Best Effort access category. The offered UDP traffic rate is set to 150 Mbit/s per station.

## Running the Simulation

The `ac-be-main.cc` file should be placed in the `scratch/` directory of a compatible ns-3 installation.

An example simulation with two DB stations and three EB stations is:

```bash
./ns3 run "scratch/ac-be-main --nDbWifi=2 --nEbWifi=3 --simulationTime=200 --enableRts=0"
```

A simulation with RTS/CTS enabled can be started using:

```bash
./ns3 run "scratch/ac-be-main --nDbWifi=2 --nEbWifi=3 --simulationTime=200 --enableRts=1"
```

The available command-line options can be displayed with:

```bash
./ns3 run "scratch/ac-be-main --PrintHelp"
```

Different ns-3 random-number runs can be selected using the standard ns-3 `RngRun` parameter.

For example:

```bash
./ns3 run "scratch/ac-be-main --nDbWifi=2 --nEbWifi=3 --RngRun=2"
```

## Simulation Output

At the end of each simulation, the program prints the aggregate throughput of the DB and EB station groups:

```text
Throughput BSS_DB: <value> Mbit/s
Throughput BSS_EB: <value> Mbit/s
```

The throughput is calculated over the measurement interval beginning after:

1. all stations have started transmitting,
2. the configured warm-up period has elapsed.

The scenario also generates separate TXOP trace files for DB and EB stations.

## TXOP Trace Files

TXOP traces use the following naming convention:

```text
txop-trace-<station-type>-<nDB>-<nEB>-<rts>.csv
```

where:

* `<station-type>` is `db` or `eb`,
* `<nDB>` is the number of DB stations,
* `<nEB>` is the number of EB stations,
* `<rts>` is `1` when RTS/CTS is enabled and `0` when it is disabled.

For example:

```text
txop-trace-db-2-3-1.csv
```

contains TXOP measurements for DB stations in a scenario with:

* two DB stations,
* three EB stations,
* RTS/CTS enabled.

Each row of a TXOP trace contains:

```text
simulation time, node identifier, TXOP start time, TXOP duration, failure status
```

The TXOP start times are used by the processing scripts to calculate the time between consecutive successful channel accesses.

## Data

The `data/` directory contains the simulation results used in the thesis.

A typical directory structure is:

```text
data/
└── <configuration>/
    ├── throughput.csv
    └── <txop-directory>/
        ├── txop-trace-db-2-3-0.csv
        ├── txop-trace-db-2-3-1.csv
        ├── txop-trace-eb-2-3-0.csv
        └── txop-trace-eb-2-3-1.csv
```

The configuration directory names identify the DB parameters or the set of experiments represented by the contained data.

### `throughput.csv`

Contains the throughput results collected for different combinations of:

* DB stations,
* EB stations,
* total station count,
* RTS/CTS configuration,
* random-number run.

The file is used by the throughput plotting scripts.

### `txop-trace-*.csv`

Contain the TXOP measurements collected during individual simulation runs.

These files are used to calculate and present the distribution of channel access delay.

## Data-Processing and Plotting Scripts

### `throughput_vs_sta_fraction.py`

Generates a multi-panel figure presenting average per-station throughput as a function of the proportion of DB and EB stations.

The figure compares several total station counts, such as 5, 10, 20, and 40 stations. Results obtained with RTS/CTS enabled and disabled can be presented in the same figure.

The input CSV path is specified directly in the script.

### `single_count_throughput_vs_fraction.py`

Generates a throughput figure for one selected total number of stations.

The script is used to present a single network size separately. The selected number of stations is defined using the `TOTAL_STA` variable.

### `ccdf_txop_latency.py`

Generates a multi-panel complementary cumulative distribution function plot for channel access delay.

Each panel represents a different combination of DB and EB stations. The script allows the delay distributions of both station types to be compared across several coexistence configurations.

The following values are configured directly in the script:

* input data directory,
* total number of stations,
* DB and EB station combinations,
* horizontal-axis range,
* RTS/CTS configuration.

### `ccdf_single_config.py`

Generates a channel access delay CCDF for one selected DB and EB station configuration.

The script is used for a detailed presentation of a particular scenario. The selected station counts and input trace files are specified directly in the script.

### `plot_config.py`

Contains the common plotting settings used by the figure-generation scripts.

The file defines elements such as:

* figure dimensions,
* font sizes,
* markers,
* line styles,
* plot formatting.

It is imported by the other Python scripts and should not be executed directly.

## Python Requirements

The data-processing scripts require Python 3 and the following packages:

```text
numpy
pandas
matplotlib
```

The required packages can be installed using:

```bash
python -m pip install numpy pandas matplotlib
```

## Generating the Figures

Before running a plotting script, the input data path and scenario parameters defined at the beginning of the file should be checked.

The scripts can be executed using:

```bash
python throughput_vs_sta_fraction.py
```

```bash
python single_count_throughput_vs_fraction.py
```

```bash
python ccdf_txop_latency.py
```

```bash
python ccdf_single_config.py
```

The generated figures are saved in the `results/` directory in SVG format.

## Reproducibility

The datasets and Python scripts included in the repository allow the figures presented in the thesis to be regenerated without rerunning the simulations.

Full reproduction of the simulation experiments additionally requires access to the private ns-3 fork containing the Deterministic Backoff implementation.
