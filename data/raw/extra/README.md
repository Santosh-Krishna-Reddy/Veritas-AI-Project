# data/raw/extra/grid_extra_PJM.csv

Written by `python -m ml.fetch_grid_extra` from the same cached EIA-930 balance files as
`data/raw/gridgreen_PJM.csv` (source and licence: see CREDITS.md, EIA-930). No network needed.
Hourly, 2024-01-01 06:00 → 2026-11-15 05:00 UTC, 25,176 rows, same timestamps as
`gridgreen_PJM.csv`. Join on `timestamp`.

Column → what it is → **when it becomes known** relative to the hour T it describes.

- `timestamp` — end of the hour, UTC (EIA "UTC Time at End of Hour"). Same convention as `gridgreen_PJM.csv`.
- `demand_forecast_mw` — PJM's own forecast of its demand for hour T (EIA "Demand Forecast (MW)"; EIA publishes no adjusted version). **Day-ahead, issue hour not recorded.** EIA's instructions say each BA submits its day-ahead forecast for day D during day D-1, but the file does not record the issue hour. EIA's about page adds that the forecast for each hour of today is typically *published* on EIA by 11:00 a.m. ET today, so via EIA it is NOT shown to be known at T − 24 h: availability unverified.
- `net_generation_mw` — PJM total net generation in hour T, all fuels (EIA "Net Generation (MW) (Adjusted)"). Published by EIA for each hour of yesterday by about 11:00 a.m. ET today.
- `total_interchange_mw` — PJM net flow to neighbours in hour T; **positive = net export** (checked: demand ≈ net generation − interchange, median gap 0.2 %). EIA "Total Interchange (MW) (Adjusted)". Published by EIA for each hour of yesterday by about 11:00 a.m. ET today.
- `miso_demand_mw` — MISO demand in hour T (EIA "Demand (MW)", the same raw column `ml/fetch.py` uses for PJM). EIA: demand is typically published about 1 h after the hour ends, so a 24 h lag is public in time.
- `miso_wind_share`, `miso_coal_share`, `miso_gas_share` — share (0–1) of MISO's positive generation in hour T from wind / coal / gas, built by `fetch.carbon_intensity()` from the `(Adjusted)` by-fuel columns, storage excluded. Published by EIA for each hour of yesterday by about 11:00 a.m. ET today.

Timing source: EIA-930 about page, "Data availability" section
(https://www.eia.gov/electricity/930-content/about.html, read 2026-11-15). The CSV itself has no
publish times, so all timing is **availability unverified** beyond that page. For the generation and
interchange columns, worst case, an hour ending 1:00 a.m. becomes public ~34 h later, so a feature for target hour T is strictly public at
T − 24 h only if it describes an hour at or before about T − 58 h. Plain 24 h lags (like the `x_*`
columns in `ml/features.py`) assume real-time access, which EIA does not promise.

Coverage (share of hours with a value): demand_forecast 99.5 %, net_generation 99.9 %,
total_interchange 99.4 %, miso_demand 99.7 %, miso shares 99.9 %. Most gaps fall on
daylight-saving change days (EIA quirk) and on the empty future hours at the end of the
newest EIA file. Gaps stay empty and are never filled with 0.
