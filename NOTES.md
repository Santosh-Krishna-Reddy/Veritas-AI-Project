# NOTES.md — session handoff (update at the end of every Claude Code session)

## State as of Sat Nov 14, ~4 PM CT
- **Real data pipeline written: `make fetch`** (ml/fetch.py) downloads EIA-930 hourly grid
  data for PJM (Jan 2024 → yesterday) + Open-Meteo weather for Chicago, computes carbon
  intensity from the fuel mix with EIA's 2023 emission factors, writes
  `data/raw/gridgreen_PJM.csv`. No API keys.
- Parser verified against the real 2026 Jul–Dec EIA file (PJM rows present, headers and
  time format match; a real hour → 439 gCO2/kWh). Locked in by tests/test_fetch.py.
- Fuel mix + weather at time t are now model features (`x_*`). `make train` saves the full
  model AND a lags-only model; `make eval` reports both, so we can say honestly whether
  the extras help.
- SPLIT_DATE = 2026-08-01 (test = Aug 2026 → latest).
- 16 tests pass. Full pipeline dry-run passed on fake data shaped like the real file.
- `make fetch` has NOT yet been run against the real internet (the Claude sandbox can't
  reach eia.gov). **Run it on a laptop first.**
- Added .gitignore (was missing): ignores eia_cache/, __pycache__, .env, processed CSVs.

## Next (in order)
1. On a laptop: `pip install -r requirements.txt && make fetch` (~5 files, 40–80 MB each,
   a few minutes). Check the printed mean carbon intensity is roughly 350–500 g/kWh.
2. `make data && make train && make eval && make failures` → commit data/raw/gridgreen_PJM.csv,
   results/metrics.json, results/failures.md together.
3. Copy real numbers into README Results (model vs persistence vs last_week vs lags_only).
   Fill the "Why" column in failures.md (check weather/holidays on those dates).
4. `make api` → curl /predict; then Gradio (`make demo`) or the Next.js shell.
5. Write-up + video + first submission by Sun 8 PM CT.

## Open bugs / limitations to state in the write-up
- Carbon intensity uses national average emission factors, direct emissions only, and
  ignores imports from neighbouring grids.
- One weather point (Chicago) for a 13-state region.
- api/main.py /predict only receives carbon-intensity history, so fuel-mix/weather features
  are NaN there; fine for the demo, but say the API uses the reduced input.

## Resume command
    pip install -r requirements.txt && make test && make fetch && make all
