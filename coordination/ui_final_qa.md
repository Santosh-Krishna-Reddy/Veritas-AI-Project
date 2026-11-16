# UI final QA — GridGreen integration (QA-MERGE)

**Date:** Nov 15, 2026 (evening CT)
**Branch:** `Santosh-Krishna-Reddy/gridgreen-qa-merge` → merged to `main`
**Target:** `origin/main` at `206d495`
**Merged branches and tips:**

| Order | Branch | Tip | Result |
|---|---|---|---|
| 1 | `gridgreen-api-contract` (API-BRIDGE) | `aa553cf` | merged as `c27111d`, 40 tests passed at that point |
| 2 | `pasted-text-content` (WEB-DESIGN) | `a8cb811` | merged as `03a0249` after resolving `api/service.py` and the shared route names |
| 3 | `gradio-dashboard-redesign` (UI-GRADIO) | `51bdf0e` | merged as `51f3f40`, clean |

No force-push was used. No model, feature, split, evaluation or results file was edited
during integration. `results/test_predictions.csv`, `results/metrics.json`,
`results/ranking_diagnosis.json`, `results/failures.md`, `ml/**` and `tests/test_split.py`
are byte-identical to `origin/main` after the merges.

## Merge conflict and namespace reconciliation

API-BRIDGE and WEB-DESIGN independently created `api/service.py` and both claimed
`GET /api/metrics` and `GET /api/failures` with different response shapes. That is a real
integration conflict, not a formatting conflict.

Resolution (commit `03a0249`):

- `api/service.py` is WEB-DESIGN's live-dashboard service (used by `web/`).
- `api/replay_service.py` is API-BRIDGE's committed-artifact replay service.
- `GET /api/replay/dates` and `GET /api/replay` keep the API-BRIDGE contract unchanged.
- API-BRIDGE's metrics/failures views moved to `GET /api/replay/metrics` and
  `GET /api/replay/failures`; `docs/ui/api_contract.md` and `tests/test_api_replay.py`
  were updated to match.
- One CORS middleware remains: `http://localhost[:port]` and `http://127.0.0.1[:port]`
  only, GET/POST, no credentials. The replay contract text was corrected to match.

Rationale: the custom dashboard is the recorded entry point, so it keeps the short
`/api/metrics` and `/api/failures` paths. The replay contract remains fully reachable
under its own prefix. No endpoint silently changed shape.

## 1. Automated tests

```text
$ make test
49 passed, 11 warnings in 3.31s
```

Warnings are pre-existing pandas deprecations in `ml/features.py` and `ml/data.py`.
Test counts by merge point: main 24 → API-BRIDGE 40 → WEB 49 → UI-GRADIO 49.

`python -m py_compile app.py api/main.py api/service.py api/replay_service.py` passed.

## 2. Decision audit reproduction

```text
$ make decision
decision reproduction: identical within 1e-9
model minus persistence: -0.3157729128487225
ci: [-1.1798364125303538, 0.5511884768736087]
days: 105 rows: 2529
```

`results/decision_metrics.json` was restored after the run, so the merge does not include
float-noise churn. The audit still reproduces the committed result and its interval still
includes zero.

## 3. Every route on the integrated FastAPI app

Run with `.venv/bin/python -m uvicorn api.main:app --port 8000` (and 8010 during QA).
All requests below returned the stated status against the merged code:

| Route | Status | Check |
|---|---:|---|
| `GET /health` | 200 | `model_trained: true` |
| `GET /api/forecast?load_kwh=7` | 200 | 24 hours, 3 cleanest, kg = 0.297 |
| `GET /api/metrics` | 200 | model/persistence metrics + verdict |
| `GET /api/failures` | 200 | 5 days, 24 hourly points in day 0 |
| `GET /api/history?days=2` | 200 | 48 hours |
| `GET /api/replay/dates` | 200 | 105 dates, 2026-08-01 → 2026-11-13; excludes incomplete 11-14 |
| `GET /api/replay?date=2026-08-01&load_kwh=7` | 200 | 24 hours, indices [15,14,13], kg 0.518 |
| `GET /api/replay/metrics` | 200 | committed metrics + decision metrics |
| `GET /api/replay/failures` | 200 | 5 grounded records from `results/failures.md` |
| `GET /docs` | 200 | OpenAPI page |
| `POST /predict` | 200 | existing 168-hour contract unchanged |

Error paths verified: forecast load `-1`, `201`, `abc` → 422; history days `0`, `31` → 422;
replay malformed date → 422; incomplete day 2026-11-14 → 404; replay load 201 → 422.

CORS verified: `localhost:3000`, `127.0.0.1:3001`, `localhost` get an allow header;
`https://evil.example`, `http://localhost.evil.example` get none.

## 4. Dashboard data: 24 timestamps, units, three real forecast-lowest hours

Both UIs were checked against `/api/forecast`, not against each other.

```text
hours: 24
consecutive hourly: True
first/last: 2026-11-14T09:00Z / 2026-11-15T08:00Z
local: 2026-11-14T03:00-06:00 → 2026-11-15T02:00-06:00 (America/Chicago)
latest real grid data: 2026-11-14T05:00Z; filled_hours = 3 (disclosed on the page)
forecast values: 326.1 .. 368.5 gCO2/kWh
lowest 3 indices: [8, 9, 7]  → 11 AM, 12 PM, 10 AM Saturday
lowest 3 values: 326.1, 326.3, 327.5
API cleanest_hours: 11 AM, 12 PM, 10 AM (same order)
dirtiest: 7 PM, 368.5 gCO2/kWh
co2_saved_kg: 0.297 (7 × (368.5 − 326.1) / 1000)
```

Independent cross-check of the Gradio path against the API: max |forecast| difference
0.0496 g/kWh and max |persistence| difference 0.0495 g/kWh, explained entirely by the
API rounding to one decimal. Both show the same window, cleanest hours and 0.297 kg.

Gradio strip uses integer rounding: 326, 326, 328; the API values are 326.1, 326.3, 327.5.
That is display rounding, not a different result.

Metrics shown by both UIs trace to `results/metrics.json`:
model MAE 13.77 / overlap 0.473, persistence 16.94 / 0.483, test 2026-08-01→2026-11-14,
2529 hours. The verdict sentence traces to `results/ranking_diagnosis.json`
(95% interval −0.051 to +0.035 includes zero).

## 5. Next.js production build and lint

```text
$ cd web && npm run lint
(no output, exit 0)

$ npm run build
▲ Next.js 16.4.6 (Turbopack)
✓ Compiled successfully in 3.5s
✓ Finished TypeScript in 1893ms
✓ Generating static pages (4/4)
Route (app)  /  /_not-found
```

Also built with `NEXT_PUBLIC_API_URL=http://localhost:8010` for isolated testing, then the
final build used the documented default `http://localhost:8000`. Production server was
run with `npm start -- -p 3000` and served the page with 0 console errors and 0 failed
requests.

## 6. Browser checks (desktop + mobile, both UIs)

Headless Google Chrome via puppeteer-core, screenshots in `.context/qa/` (not committed)
and the original agent set in `docs/ui/`.

| UI | Viewport | 24 cells | 3 ranked | horizontal overflow | console errors | failed requests |
|---|---|---:|---:|---:|---:|---:|
| Next.js | 1440×900 light | 24 | 3 | 0 | 0 | 0 |
| Next.js | 1440×900 dark | 24 | 3 | 0 | 0 | 0 |
| Next.js | 1920×1080 dark | 24 | 3 | 0 | 0 | 0 |
| Next.js | 390×844 light | 24 | 3 | 0 | 0 | 0 |
| Next.js | 320×700 light | 24 | 3 | 0 | 0 | 0 |
| Gradio | 1440×900 | 24 | 3 | 0 | 0 | 0 |
| Gradio | 390×844 | 24 | 3 | 0 | 0 | 0 |

Next.js interaction checks: preset 3 kWh → 0.13 kg; 7 kWh → 0.30 kg; invalid 99999 →
range message, kg hidden, no request; table toggle → 24 rows; Tab reaches the first hour
cell in 5 presses, focus outline is 2px solid teal, and the live readout updates
(“Sat 3 AM: 341.9 g/kWh … saves 0.19 kg”). Recharts SVG is focusable (`tabindex=0`) and
uses `:focus-visible` styling.

Gradio interaction check: default 7 kWh shows 0.30 kg; 40 kWh EV preset updates the
illustrative difference; 24 cells and 3 ranked markers render at both widths. On mobile
the strip scrolls horizontally with an explicit hint; that is the main UX difference from
the Next page, which wraps the 24 cells into 3 rows.

## 7. Failure states

- **API offline** (Next.js; `/api/*` aborted): only the “forecast service is not running”
  alert renders, with the command to start it. No numbers, no tables
  (`docs/ui/break/api-down.png`, `.context/qa/next-api-offline.png`).
- **Model artifact missing** (Next.js; `/api/forecast` returns the real 503 body
  `model not trained yet: run make train`): explicit “The model or data is missing” alert;
  held-out metrics and failure analysis still render from `results/`
  (`.context/qa/next-missing-model.png`). Reproduced with a second API process whose
  `MODEL_PATH` pointed at a nonexistent file; `/health` reported `model_trained: false`.
- **Model artifact missing** (Gradio; `run_forecast` with `MODEL_PATH` absent): setup
  panel, empty plot, “No forecast values have been substituted”, and the `make train`
  instruction. Verified by direct function call, not by moving the real artifact.
- Invalid load: Next page shows a range message and hides kg claims; the API independently
  returns 422. Gradio enforces 0.5–60 kWh in `run_forecast` and shows its error panel.

## 8. Security

```text
git log -p --all | grep -cE '(EIA_API_KEY|api_key)=[A-Za-z0-9]{20,}'  -> 0
tracked .env files                                                     -> none
tree scan for key assignments (excluding .env/.git/.venv/node_modules) -> no hits
```

The only matches in the diff are the words “token”/“key” inside the WEB agent's own
security-report text and `js-tokens` in `package-lock.json`. `web/` reads only
`NEXT_PUBLIC_API_URL`; no secrets are embedded. CORS remains local-only. The repo is
public and the existing `.env` is ignored.

## 9. Credits

`CREDITS.md` now includes every newly used item:

- Python: FastAPI/Starlette CORSMiddleware, openpyxl 3.1.5.
- Web: Next.js 16, React 19, Tailwind CSS 4, shadcn/ui, cn, Base UI, Recharts 3,
  lucide-react, class-variance-authority, tw-animate-css, ESLint, TypeScript.
- Fonts: IBM Plex Sans / Sans Condensed / Mono (SIL OFL).
- AI/QA tools: Claude Code, ChatGPT, Claude Code plugins and the `frontend-design`
  skill; puppeteer-core and Google Chrome as non-shipped QA tools.
- Data: EIA extra balance-file columns, PJM CO₂ cross-check workbook.

`coordination/credits.d/WEB.md` and `credits.d/DATA-GRID.md` remain as provenance; the
submission file is the merged `CREDITS.md`.

## 10. Demo honesty

- Both UIs label the window a **historical replay**. The Next page gained a visible
  “Historical replay” badge and the sentence “Historical replay of … — not a live
  forecast.” The Gradio header already said “HISTORICAL REPLAY · NOV 14, 3 AM–NOV 15,
  2 AM 2026 CT”.
- The Next page now says the kg figure is a **modeled average-intensity difference,
  not measured or verified avoided emissions**, next to the number. Gradio already
  labelled it “Illustrative load difference” and “not guaranteed CO₂ savings”.
- The main scientific finding is not softened: both UIs state MAE 13.77 vs 16.94 and
  overlap 0.473 vs 0.483, with the tie interval. The custom page's verdict sentence is
  generated from the committed metrics, not hard-coded prose.
- The 3 gap-filled hours after 2026-11-14 05:00 UTC are disclosed on the page.

## 11. Gradio chart bug found and fixed during integration

The merged UI-GRADIO chart sorted its categorical x-axis as a fixed 12 AM→11 PM clock
list. The replay window is 3 AM Saturday → 2 AM Sunday, so Sunday's first three hours
were drawn at the left of the chart and Saturday's 3 AM point jumped in after them. That
was a real visual misrepresentation of chronological order.

Fix in `app.py` (commit with this QA pass): derive `INITIAL_SORT` from the actual target
timestamps and pass it to `gr.LinePlot(sort=...)`; the axis now runs 3 AM, 4 AM, …,
11 PM, 12 AM, 1 AM, 2 AM. Verified in the browser; the chart and strip now agree in order.

## 12. Final decision: custom Next.js dashboard

**Chosen for the recorded demo:** `web/` + `make api`.

Reasons: it works end-to-end on the documented default ports, passed production build,
lint, desktop/mobile browser checks, break tests and traceability; it is substantially
more legible and better designed than the Gradio page (24 cells in 3 rows on mobile
instead of horizontal scrolling, clearer hierarchy, no dashboard chrome); and its
numbers are generated by the same Python service and committed artifacts.

**Fallback:** `make app` (redesigned Gradio). It works, is honest, and needs only one
process. It is documented in `SUBMISSION.md`, `README.md`, `QUICKSTART.md` and
`docs/video_script.md`.

## Exact run commands (documented entry point)

```bash
# once
uv venv --python 3.12
uv pip install -r requirements.txt
make data train eval rank failures decision

# demo
make api                                  # terminal 1: http://localhost:8000
cd web && npm install && npm run dev      # terminal 2: http://localhost:3000
```

Production: `cd web && npm run build && npm start`.
Fallback: `make app` → http://127.0.0.1:7860.

## Unresolved issues / limits (honest list)

1. `npm audit` reports 12 advisories in dev/transitive packages (2 low, 10 moderate).
   `npm audit fix --force` would change major versions; not applied. Not runtime code
   written by us.
2. Next.js 16 is used even though `CLAUDE.md` §4 mentions 14 (wave-2 prompt said to use
   current versions). Be ready to say “Next.js 16” to a judge.
3. Gradio 6's native chart still prints two non-blocking Vega warnings (spec v5.17 vs
   renderer v6.4.2; categorical `zero` dropped). Rendering and interaction are unaffected.
4. The Gradio strip scrolls horizontally on phones; the Next page wraps to 3 rows.
   Acceptable, but the Next page is the better mobile experience.
5. `make pipeline` was not re-run from `make fetch` in this worktree; `make test` and
   `make decision` ran against the existing processed data and committed predictions.
   WEB-DESIGN's fresh-clone run (documented in `docs/ui_notes.md`) reproduced
   `results/metrics.json` and `results/failures.md` byte-for-byte with seed 42.
6. Three final test hours are gap-filled; disclosed in both UIs and the README.
   The last partial UTC day is excluded from replay dates and day metrics.
7. The request to drop trailing gap-filled hours (`ml/data.py`) remains rejected for this
   submission (3/2529 rows); documented as a limitation.
8. Human-only submission fields remain: school/email, team rows, “New to AI?”,
   demo video URL, and confirmation that every member contributed.
9. The old background servers on ports 3000/7860/8000 from earlier agent sessions were
   stopped so `make api` and `npm start` bind to the documented ports. The QA servers
   left running are on 8000 (API) and 3000 (Next production).
