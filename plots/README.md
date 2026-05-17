# How to Generate Figures

## Quick Start

1. Navigate to the `plots` directory:
   ```bash
   cd plots
   ```

2. Edit the desired script to set your parameters:
   - Data source path (DATA_DIR or CSV file path)
   - Station counts (TOTAL_STA, N_DB, N_EB, or configs)
   - X-axis limits (X_LIM) if needed
   - Which RTS/CTS modes to display (comment/uncomment lines in the script)

3. Run the script:
   ```bash
   python throughput_vs_sta_fraction.py
   python single_count_throughput_vs_fraction.py
   python ccdf_txop_latency.py
   python ccdf_single_config.py
   ```

4. Output figures are saved in `results/` directory as SVG files.

## Available Scripts

- **throughput_vs_sta_fraction.py** - Throughput across 4 STA counts (5, 10, 20, 40)
- **single_count_throughput_vs_fraction.py** - Throughput for one fixed STA count
- **ccdf_txop_latency.py** - CCDF latency for multiple DB/EB configurations
- **ccdf_single_config.py** - CCDF latency for single DB/EB mix

See `PLOT_GENERATION_GUIDE.md` for detailed instructions on each script.

