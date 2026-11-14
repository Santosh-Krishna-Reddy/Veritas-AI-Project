# NOTES.md — session handoff (update at the end of every Claude Code session)

## State as of Sat Nov 14, ~12:10 PM CT
- Repo scaffolded: CLAUDE.md, .claude/settings.json, README template, CREDITS, Makefile.
- ML pipeline written and tested on SYNTHETIC data: `make data` (needs `--synthetic` or real
  CSVs in data/raw/), `make train`, `make eval`, `make failures`. 8 tests pass (`make test`).
- Region defaulted to PJM (ml/config.py). Change ELECTRICITY_MAPS_ZONE + REGION_NAME if needed.
- api/main.py and ml/demo.py written but NOT yet run (FastAPI/Gradio not installed where
  they were written). First thing: `pip install -r requirements.txt && make train && make api`.

## Next (in order)
1. Download real hourly carbon-intensity CSV for the region into data/raw/ (Electricity Maps
   zone US-MIDA-PJM, or EIA grid monitor). Check the column names match RAW_COLUMN_MAP in
   ml/config.py. Set SPLIT_DATE so the test period is the last ~3 months. Add to CREDITS.md.
2. `make data && make train && make eval` on REAL data. Copy metrics into README Results.
3. `make failures`, fill in the "Why" column, copy into README.
4. Add weather features (Open-Meteo historical: temp, wind, solar radiation) in ml/features.py
   — this is the most likely way to beat persistence. Measure before/after.
5. `make api` -> curl /predict works. Then Gradio demo (`make demo`) or Next.js shell.
6. README + video + submit by Sun 8 PM CT.

## Open bugs
- none known

## Resume command
    pip install -r requirements.txt && make test && make data -- --synthetic
