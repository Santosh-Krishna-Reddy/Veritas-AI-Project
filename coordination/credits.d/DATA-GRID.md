# DATA-GRID credits (to merge into CREDITS.md)

- EIA-930 balance files, extra columns (Demand Forecast, Net Generation (Adjusted), Total
  Interchange (Adjusted)) for PJM and all columns for MISO. Same dataset already credited
  in CREDITS.md. U.S. government data, public domain (EIA copyright & reuse:
  https://www.eia.gov/about/copyrights_reuse.php).
- EIA-930 per-BA Excel file for PJM ("Published Hourly Data" sheet: hourly CO2 Emissions
  Generated, CO2 Factor columns), used only for results/ci_crosscheck.json:
  https://www.eia.gov/electricity/gridmonitor/knownissues/xls/PJM.xlsx (downloaded
  2026-11-15). Public domain, same EIA reuse page. Data-availability timing taken from
  https://www.eia.gov/electricity/930-content/about.html
- openpyxl 3.1.5 (reads the .xlsx above), MIT licence: https://openpyxl.readthedocs.io/
  Installed with `uv pip install openpyxl`; only the one-off `--crosscheck` step needs it.
