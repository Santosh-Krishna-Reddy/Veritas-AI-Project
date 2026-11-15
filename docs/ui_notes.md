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
