# Web page notes (WEB agent, Sun Nov 15)

Serves finals **Demo & clarity (30)** and the Round 1 video (**Communication, 15**). The page earns
nothing by itself; it shows the model's answer and its held-out test results.

## Routes (api/main.py → api/service.py, tests in tests/test_api_web.py)
| Route | Source |
|---|---|
| `GET /api/forecast?load_kwh=7` (0–200) | model + last 192 h of `data/processed/`, `ml/recommend.py` |
| `GET /api/metrics` | `results/metrics.json` + `ranking_diagnosis.json` (+ `decision_metrics.json`, `ablation.json` when they exist) and a verdict sentence built from those numbers |
| `GET /api/failures` | worst days in `results/failure_features.csv`, per-day MAE from `test_predictions.csv` via `ml.failures.daily_errors`, explanation text from `results/failures.md` |
| `GET /api/history?days=7` (1–30) | last N×24 hours of `data/processed/` |

## Decisions made without asking
- **"Tomorrow" wording.** Our data ends at 2026-11-14 08:00 UTC (EIA lag), so the forecast is for
  the 24 hours *after the latest data*, not literally tomorrow. The page says so and prints the
  data-through timestamp instead of claiming "tomorrow".
- **Forecast logic copied from app.py.** `_forecast_next_24h` is mirrored in `api/service.py`,
  because importing `app.py` pulls in Gradio (~30 s cold start). Same features, same model.
- **lo/hi are null.** `ml/predict.py` has not shipped. Switching is one place: `forecast()` in
  `api/service.py`. The chart draws the 10–90 % band automatically when lo/hi are present and
  says "no uncertainty band yet" when they are not.
- **Verdict sentence lives in Python** (`service.verdict`), so the wording follows the numbers. It
  says "ties" when the bootstrap 95 % interval of the overlap gap (from `ranking_diagnosis.json`)
  includes 0, otherwise "beats"/"loses to". Unit-tested both ways.
- **Table shows 4 rows** (persistence, last week, lags-only model, full model). The ranking
  experiments (`model_rank`, `model_deviation*`) are left off the page; they are in the README.
- `decision_metrics.json` / `ablation.json` are passed through by `/api/metrics` but not drawn:
  their format did not exist yet.
- **Failure day axis is UTC**, matching `results/failures.md` (days are UTC target days).
- Presets (7 / 3 / 1.5 kWh) are illustrative, labelled as such on the page and in `web/lib/presets.ts`.
- context7 and chrome-devtools-mcp were not available in this session. Scaffolded with
  `create-next-app@latest` (Next 16.4, Tailwind 4) and `shadcn@latest` (base-nova); screenshots and the
  console/network check used `puppeteer-core` driving local Chrome (scratch script, not committed).
- Fixed a scaffold bug: shadcn wrote `--font-sans: var(--font-sans)` (self-reference → serif
  fallback); now points at Geist.

## States
Loading (skeletons) · API down (one plain message, nothing else rendered) · model/data missing
(the API's 503 text, e.g. "model not trained yet: run `make train`") · load out of range
(inline message, no request sent; the API also rejects it with 422).

## Known display limits
- The last 3 hours of `test.csv` are gap-filled copies (already disclosed in the README), so the
  persistence line is flat at the end of the window.
- Leakage: the page adds no features. The forecast uses the existing model inputs as built by
  `ml/features.py` (same as `app.py`).
