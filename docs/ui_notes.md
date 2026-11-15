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
  fallback). The design pass replaced the fonts with IBM Plex anyway.

## States
Loading (skeletons) · API down (one plain message, nothing else rendered) · model/data missing
(the API's 503 text, e.g. "model not trained yet: run `make train`") · load out of range
(inline message, no request sent; the API also rejects it with 422).

## Known display limits
- The last 3 hours of `test.csv` are gap-filled copies (already disclosed in the README), so the
  persistence line is flat at the end of the window.
- Leakage: the page adds no features. The forecast uses the existing model inputs as built by
  `ml/features.py` (same as `app.py`).

## Design pass (Sun Nov 15): "a tide table for the grid"

Who: a Chicago-area household or school facilities manager at ~8 PM setting a timer for an EV
charger, dryer or dishwasher; and a judge watching a 1080p screen recording. Screenshots:
`docs/ui/{light,dark}-{1440x900,1920x1080,390x844}.png` (viewport only; 0 console errors, 0 failed
requests on all six). No number, route or result sentence changed. The forecast API gained one
field, `hours[].saved_kg`, so the hover readout's kg figure is computed in Python, not TypeScript.

### Palette (CSS variables in `web/app/globals.css`)
| Token | Light | Dark | Use |
|---|---|---|---|
| `--paper` | `#f3f5f4` | `#0e1820` | page |
| `--ink` | `#14202b` | `#e4eaee` | text, cleanest-cell outline |
| `--ink-2` | `#46535f` | `#9fb0bc` | secondary text, "tomorrow = today" line |
| `--rule` | `#c9d1d6` | `#2a3b47` | hairlines, borders |
| `--clean` | `#0b6b6b` | `#5cc4ba` | forecast line, focus outline |
| `--dirty` | `#a3441f` | `#e8875c` | errors, dirtiest-cell dashed outline |
| `--scale-1…5` | `#7fc8bf #bfe0d8 #e6e3d3 #edbe7e #d9845a` | `#0f5a58 #23474a #3a3f3c #6b4a1e #84391e` | hour-strip tints, cleanest → dirtiest |

Contrast (WCAG, checked with a script): every text pair is ≥ 4.5:1. Lowest: ink on `--scale-5`
5.82 (light), ink on `--scale-1` 6.59 (dark). Body ink on paper ≈ 15:1 in both themes.

### Type scale (ratio 1.25 from a 16 px body)
`--step--1` 12.8 px (labels, axis, cells) · `--step-0` 16 px (body) · `--step-1` 20 px (section
headings, second answer line) · `--step-2` 25 px · `--step-3` 31 px · `--step-4` 39 px (answer on
desktop; it scales from step-2 on phones with `clamp`). IBM Plex Sans Condensed for headings,
Plex Sans for text, Plex Mono with tabular figures for every number (`.num` and `<When>`), so
columns of numbers line up.

### Three design decisions, and why
1. **The hour strip is the centre of the page.** People already pick an hour from a tide table, and
   carbon intensity rises and falls once a day the same way. 24 cells with the hour and value
   *printed* in each answer "when?" faster than a line chart: you read the numbers instead of
   guessing heights. The chart and strip share one "pointed-at hour": hover or Tab to a cell
   and the chart draws a line at that hour; the readout under the strip gives g/kWh and the kg
   saved for the current load.
2. **Meaning never rests on colour alone.** Colour shows *how* clean an hour is (5 steps, teal →
   neutral → amber → rust, so it also reads for red-green colour blindness), but the decision is
   carried by shape and text: the 3 cleanest cells have a solid outline and a rank number
   underneath (matching the numbered diamonds on the chart); the dirtiest has a dashed outline;
   the two chart lines differ by solid vs dashed; every cell has a full spoken label
   ("Sat 11 AM: 326.1 grams per kilowatt-hour, cleanest hour number 1"); and a "Show the 24
   hours as a table" toggle gives the chart's numbers as text.
3. **Numbers in mono, calm everywhere else, one motion.** Tabular mono digits make 342/347/350
   line up like a printed timetable, so you can compare hours at a glance. We removed the
   default dashboard chrome (cards, shadows, a green callout box, leaf-green) because an
   "eco-app" look makes a weak result look like marketing. The only animation is the kg figure
   and the three cleanest cells settling in together when the load changes, so you can see what
   your input changed. It is switched off under `prefers-reduced-motion`.

Other calls: dark theme follows the OS setting (no toggle); the strip's day names appear only
where a day starts (like a tide table's date line); the strip covers the 24 forecast hours, which
start after our latest data, not midnight-to-midnight "tomorrow"; Recharts' focusable chart
SVG got a visible focus outline (it hid it by default).

## Review pass (Sun Nov 15)

All six checks pass. Commits: `135bc8a` (review fixes), `a8cb811` (input honesty, no
dangerouslySetInnerHTML, README setup). Everything below is pasted command output.

### 1. /code-review — 10 findings, 7 fixed, 3 out of scope
| # | Finding | Status |
|---|---|---|
| 1 | Out-of-order forecast responses could overwrite newer ones (stale kg for a different load) | **Fixed**: `page.tsx` effect drops answers from superseded requests (`live` flag) |
| 2 | NaN in `failure_features.csv` would make `/api/failures` a 500 (JSON has no NaN) | **Fixed**: `_records()` turns NaN into null; test `test_records_turns_nan_into_null` |
| 3 | API-down alert gave no way back | **Fixed**: message now says "Start it with: make api, then reload this page" |
| 4 | CORS allowed only port 3000; `next dev` on 3001 looked like "API down" | **Fixed**: `allow_origin_regex` = localhost / 127.0.0.1, any port (still local only, see 5) |
| 5 | Model re-loaded from disk on every request | **Fixed**: `functools.lru_cache` on `_model()` (same caching as `main.model()`) |
| 6 | Forecast pad/ffill logic copied in 3 places (app.py, /predict, service.py) | Not fixed: the shared home is `ml/` (MODEL agent's `ml/predict.py`), outside WEB paths |
| 7 | Page called the 3 gap-filled hours "our latest grid data" | **Fixed**: `data_through_utc` = last REAL hour from `data/raw/gridgreen_PJM.csv` (05:00 UTC); new `filled_hours` (3) is stated on the page |
| 8 | `verdict()` said "loses to" when overlaps were equal | **Fixed**: equal → "ties"; test added |
| 9 | New libraries are in `coordination/credits.d/WEB.md`, not `CREDITS.md` | Not fixed here: the wave-2 prompt routes credits through credits.d; WRITEUP owns `CREDITS.md`. **Must be merged before submission.** |
| 10 | Next.js 16 instead of the 14 named in CLAUDE.md §4 | Not changed: the wave-2 prompt said to scaffold with current versions. `cacheComponents` / `partialPrefetching` in `next.config.ts` are create-next-app 16.4 defaults. Team should be ready to say "Next.js 16" to a judge. |

Also changed during the pass: while the kWh box holds an invalid value, the kg sentence, the
readout's kg clause and the table's kg column are hidden (they were computed for the last valid
load and would sit next to a different number). Found in check 4.

### 2. Trace: every number in `docs/ui/*.png` → API field → file / model output
| On the page | API field | Source |
|---|---|---|
| "Run it at 11 AM, 12 PM or 10 AM … Saturday" | `/api/forecast` `cleanest_hours` | `ml.recommend.recommend` on predictions of `ml/artifacts/model.joblib` over the last 192 h of `data/processed/` |
| "dirtiest hour (Sat 7 PM)" | `dirtiest_hour` | same |
| "7 kWh" | `load_kwh` | the user's input, echoed by the API |
| "0.30 kg of CO₂" | `co2_saved_kg` | `ml.recommend.recommend` |
| "Sat 3 AM to Sun 2 AM" | `hours[0].ts_local`, `hours[23].ts_local` | last processed hour + 1…24 h |
| "2026-11-14 05:00 UTC", "the 3 hours after it" | `data_through_utc`, `filled_hours` | last non-empty CI in `data/raw/gridgreen_PJM.csv`; end of `data/processed/` minus that |
| Chart line, strip values (342 … 347), table column 2 | `hours[].forecast` | `model.joblib` predictions |
| Dashed line, table column 3 | `hours[].persistence` | `ml.baseline.persistence` |
| Readout "326.1 g/kWh … saves 0.30 kg", table column 4 | `hours[i].forecast`, `hours[i].saved_kg` | `(max forecast − hour) × kWh / 1000`, the `ml/recommend.py` formula |
| Diamonds / ranks 1 2 3, outlines | order of `cleanest_hours` | same as headline |
| Strip legend 326 … 369 | min / max of `hours[].forecast` (rounded for display) | model predictions |
| Y-axis ticks 320 … 400, failure-chart ticks 330 … 450 | Recharts auto-scale of the plotted values | API data |
| "2026-08-01 to 2026-11-14 (2529 hours)" | `/api/metrics` `metrics._meta` | `results/metrics.json` |
| Table 16.94/0.483, 28.43/0.387, 15.18/0.448, 13.77/0.473 | `metrics.<key>.mae / cleanest_3_overlap` | `results/metrics.json` |
| Verdict 13.77, 16.94, 0.473, 0.483, −0.051, +0.035 | `verdict` | `results/metrics.json` + `results/ranking_diagnosis.json` (`bootstrap_95ci`) |
| "Wed 2026-10-14", "29.9 gCO₂/kWh", "persistence: 36.1" | `/api/failures` `days[0]` | `ml.failures.daily_errors` over `results/test_predictions.csv` (worst = max model MAE) |
| Failure paragraph and pattern paragraph (30, 12, 375 → 411, +36, 17 %, 24 → 19, 1.02x, 6.4 % → 3.3 %, 1.16x, 5 of 5, 18-48 g, 45 %, 13-state) | `days[0].explanation`, `pattern` | verbatim from `results/failures.md` |
| Failure chart (24 × 3 values) | `days[0].hours` | `results/test_predictions.csv` |
| Presets 7 / 3 / 1.5 kWh, limit 0–200 | none | `web/lib/presets.ts`, labelled illustrative on the page; bounds match `api/main.py` |
| "24 hours", "3 cleanest", "10–90 %", "EIA (2023)", "CC BY 4.0" | none | fixed labels and source names, not results (`HORIZON_HOURS`, `CLEANEST_K` in `ml/config.py`) |

Nothing was untraceable, so nothing was removed. Automated check (`.context/trace.py`) recomputes
each value independently (re-running the model through `app.py`'s own forecast function and
re-reading the files) and compares with the live API:
```
PASS  24 hourly forecasts (strip, chart, table)    shown=341.9..346.6                       source=ml/artifacts/model.joblib via app.py
PASS  persistence line                             shown=334.8                              source=ml.baseline.persistence
PASS  3 cleanest hours (headline, diamonds, outlines) shown=['11:00', '12:00', '10:00']        source=ml.recommend.recommend
PASS  dirtiest hour                                shown=19:00                              source=ml.recommend.recommend
PASS  kg CO2 saved (headline)                      shown=0.297                              source=ml.recommend.recommend
PASS  kg saved per hour (readout, table)           shown=0.186                              source=same formula as recommend
PASS  latest real grid data                        shown=2026-11-14T05:00:00+00:00          source=data/raw/gridgreen_PJM.csv
PASS  gap-filled hours                             shown=3                                  source=data/processed/ end - raw last
PASS  forecast window start / end                  shown=2026-11-14T03:00 / 2026-11-15T02:00 source=last processed hour + 1..24
PASS  table row persistence                        shown=16.94 / 0.483                      source=results/metrics.json
PASS  table row last_week                          shown=28.43 / 0.387                      source=results/metrics.json
PASS  table row model_lags_only                    shown=15.18 / 0.448                      source=results/metrics.json
PASS  table row model                              shown=13.77 / 0.473                      source=results/metrics.json
PASS  test period + hours                          shown=2026-08-01 to 2026-11-14 (2529)    source=results/metrics.json _meta
PASS  verdict sentence numbers                     shown=13.77 16.94 0.473 0.483 -0.051 +0.035 source=metrics.json + ranking_diagnosis.json
PASS  worst day                                    shown=2026-10-14                         source=max model_mae in test_predictions.csv
PASS  worst-day model / persistence MAE            shown=29.9 / 36.1                        source=results/test_predictions.csv
PASS  explanation paragraph (all its numbers)      shown=Level offset: under-predicted ...  source=results/failures.md
PASS  pattern paragraph (all its numbers)          shown=5 of 5 days are level offsets ...  source=results/failures.md
PASS  failure chart 24 x 3 values                  shown=24                                 source=results/test_predictions.csv
```

### 3. Hard-coded result digits in web/ — none
`grep` for decimals, percentages, kg and g/kWh in `web/app`, `web/components`, `web/lib`
(excluding vendored `components/ui/`):
```
app/page.tsx:127:0.5
components/forecast-chart.tsx:12:–90 %
components/forecast-chart.tsx:54:0.15
components/hour-strip.tsx:25:0.5
components/hour-strip.tsx:45:0.75
```

All five are styling or input settings: input `step={0.5}`, the band label "10–90 %" (shown only
when the API sends lo/hi), band `fillOpacity={0.15}`, Tailwind `gap-0.5`, cell font `0.75rem`. The
wider scan of every digit literal (60 lines) found only layout sizes, SVG geometry, ISO-string
slicing, the 5 colour steps, rank `i + 1`, the presets file and the debounce delay (300 ms). The
default kWh now comes from `PRESETS[0]` instead of a literal "7".

### 4. Break it on purpose
**4a. API stopped** — `docs/ui/break/api-down.png`. Only the alert is shown; no numbers.
```
{"console_errors": 3 x "Failed to load resource: net::ERR_CONNECTION_REFUSED" (expected),
 "failed_requests": [/api/metrics, /api/failures, /api/forecast?load_kwh=7  net::ERR_CONNECTION_REFUSED],
 "visible_text": "The forecast service is not running | Cannot reach the GridGreen API at http://localhost:8000.
   Start it with: make api, then reload this page. Nothing else is shown until the service answers."}
```
**4b. `ml/artifacts/model.joblib` missing** (scratch copy `.context/scratch-nomodel/` with the file
left out; the real artifact was never touched) — `docs/ui/break/model-missing.png`. The forecast
block is replaced by the API's own message; the test results and failure day still show, because
they come from `results/`, not the live model.
```
$ curl localhost:8000/health
{"status":"ok","region":"PJM (Chicago / mid-Atlantic grid)","model_trained":false}
$ curl "localhost:8000/api/forecast?load_kwh=7"
{"detail":"model not trained yet: run `make train`"}  HTTP 503
metrics HTTP 200
failures HTTP 200
```
```
{
 "out": "model-missing.png",
 "horizontal_overflow_px": 0,
 "console_errors": [
  "Failed to load resource: the server responded with a status of 503 (Service Unavailable)"
 ],
 "failed_requests": [
  "http://localhost:8000/api/forecast?load_kwh=7 HTTP 503"
 ],
 "input_value": "7",
 "visible_text": "The model or data is missingmodel not trained yet: run `make train` | The buttons use typical round numbers, not measurements. Type your own if you know it."
}
```

**4c. load_kwh = −1 and 99999.** API:
```
$ curl "localhost:8000/api/forecast?load_kwh=-1"
{"detail":[{"type":"greater_than_equal","loc":["query","load_kwh"],"msg":"Input should be greater than or equal to 0",...}]}  HTTP 422
$ curl "localhost:8000/api/forecast?load_kwh=99999"
{"detail":[{"type":"less_than_equal","loc":["query","load_kwh"],"msg":"Input should be less than or equal to 200",...}]}  HTTP 422
```
Page (typed into the box; no request is sent, the kg claims disappear, the hours stay because
they do not depend on the load) — `docs/ui/break/kwh-minus1.png`, `kwh-99999.png`:
```
{
 "out": "kwh-minus1.png",
 "horizontal_overflow_px": 0,
 "console_errors": [],
 "failed_requests": [],
 "input_value": "-1",
 "visible_text": "Run it at 11 AM, 12 PM or 10 AM on Saturday (cleanest first). | Enter a number from 0 to 200 kWh."
}
{
 "out": "kwh-99999.png",
 "horizontal_overflow_px": 0,
 "console_errors": [],
 "failed_requests": [],
 "input_value": "99999",
 "visible_text": "Run it at 11 AM, 12 PM or 10 AM on Saturday (cleanest first). | Enter a number from 0 to 200 kWh."
}
```

**4d. 320 px wide** — `docs/ui/break/width-320.png` (full page): no horizontal scroll
(`horizontal_overflow_px: 0`), 0 console errors, 0 failed requests; the strip wraps to rows of 8,
the table's method names wrap.

### 5. Security
```
$ grep -n "allow_origin\|CORSMiddleware" api/main.py
73:from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
79:app.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
Origin http://localhost:3000          -> access-control-allow-origin: http://localhost:3000

Origin http://127.0.0.1:3001          -> access-control-allow-origin: http://127.0.0.1:3001

Origin http://localhost               -> access-control-allow-origin: http://localhost

Origin https://evil.example           -> 
Origin http://localhost.evil.example  -> 
Origin http://192.168.1.5:3000        -> 
Preflight POST from localhost:3000 -> HTTP 400
$ grep -rniE "(api[_-]?key|secret|token|password|bearer|sk-[a-z0-9]{10})" web (excluding node_modules, .next)
web/app/globals.css:9:   GridGreen tokens. "A tide table for the grid": ink on cool paper, and one
web/app/globals.css:34:  /* shadcn/ui tokens mapped onto ours, so its components inherit the palette. */
web/package-lock.json:53:        "js-tokens": "^4.0.0",
web/package-lock.json:6238:    "node_modules/js-tokens": {
web/package-lock.json:6240:      "resolved": "https://registry.npmjs.org/js-tokens/-/js-tokens-4.0.0.tgz",
web/package-lock.json:6742:        "js-tokens": "^3.0.0 || ^4.0.0"
$ grep -rn "dangerouslySetInnerHTML" web (excluding node_modules, .next)
(no matches outside the comment explaining its removal)
$ git ls-files | grep -iE "(^|/)\.env"
(no tracked .env files)
$ grep -n "env" .gitignore web/.gitignore
.gitignore:5:.venv/
.gitignore:6:venv/
.gitignore:9:.env
web/.gitignore:33:# env files (can opt-in for committing if needed)
web/.gitignore:34:.env*
web/.gitignore:41:next-env.d.ts
$ grep -rn "process.env" web/app web/components web/lib
web/lib/api.ts:3:export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
```

CORS: only `http://localhost[:port]` and `http://127.0.0.1[:port]` get an allow header
(`fullmatch`, so `localhost.evil.example` is refused); GET only, so a browser preflight for
POST is rejected (400). Secret grep: the only hits are the word "tokens" in CSS comments and the
`js-tokens` package. `dangerouslySetInnerHTML`: the one use was in vendored
`components/ui/chart.tsx`; replaced with a plain `<style>` text child (the CSS comes only from
static chart config). `.env*`: none tracked; `web/.gitignore` ignores `.env*`, the root ignores `.env`.

### 6. Fresh clone, following web/README.md word for word
```
$ git clone --branch Santosh-Krishna-Reddy/pasted-text-content <this repo> <tmp>/clone
a8cb811 fix: hide kg claims while load input is invalid, drop dangerouslySetInnerHTML, complete web README setup
$ uv venv --python 3.12 && uv pip install -r requirements.txt
 + urllib3==2.8.0
 + uvicorn==0.54.0
$ make data train eval rank failures
clean: 25155 hourly rows, 27 gap hours interpolated/dropped
train: 22626 rows 2024-01-01 -> 2026-07-31
test:  2529 rows 2026-08-01 -> 2026-11-14
trained on 22458 rows, 38 features
trained on 22458 rows, 28 features
saved <tmp>/clone/ml/artifacts/model.joblib and <tmp>/clone/ml/artifacts/model_lags_only.joblib
  "model_deviation": {
    "mae": 14.200628021383613,
  "model_deviation_today_mean": {
    "mae": 19.265933569063286,
  "model_rank": {
    "mae": 19.40128655324754,
    "mae": 16.937007694349827,
    "mae": 28.430873733284734,
  "model": {
    "mae": 13.768439399947058,
  "model_lags_only": {
    "mae": 15.180547069739413,
    "test_rows": 2529,
    "model": 0.828807901738386,
make data train eval rank failures 2>&1  109.60s user 43.16s system 268% cpu 56.841 total
$ diff results/metrics.json <original repo>/results/metrics.json
(identical)
$ diff results/failures.md <original>
(identical)
```

```
$ make api   (terminal 1)
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
$ cd web && npm install && npm run dev   (terminal 2)
  npm audit fix --force

Run `npm audit` for details.
- Local:         http://localhost:3000
✓ Ready in 258ms
✓ Running next.config.ts took 1756ms
$ curl localhost:8000/health
{"status":"ok","region":"PJM (Chicago / mid-Atlantic grid)","model_trained":true}
$ open http://localhost:3000 (headless Chrome)
{
 "out": "fresh-clone.png",
 "horizontal_overflow_px": 0,
 "console_errors": [],
 "failed_requests": [],
 "input_value": "7",
 "visible_text": "Run it at 11 AM, 12 PM or 10 AM on Saturday (cleanest first). | The buttons use typical round numbers, not measurements. Type your own if you know it."
}
```

Screenshot: `docs/ui/break/fresh-clone.png`. The clone's results are byte-identical to the
committed ones (seed 42). `npm install` reports 7 moderate advisories in dev dependencies
(`npm audit`); not addressed, as `npm audit fix --force` would change major versions.

### Screenshots
`docs/ui/{light,dark}-{1440x900,1920x1080,390x844}.png` retaken after these fixes; all six:
```
light-1440x900 console errors: 0 [] failed requests: 0 []
light-1920x1080 console errors: 0 [] failed requests: 0 []
light-390x844 console errors: 0 [] failed requests: 0 []
dark-1440x900 console errors: 0 [] failed requests: 0 []
dark-1920x1080 console errors: 0 [] failed requests: 0 []
dark-390x844 console errors: 0 [] failed requests: 0 []
```
