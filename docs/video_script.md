# GridGreen demo video: 90-second historical replay script

Target length 1:30 (the hard limit is 2:00). Screen recording of the **custom Next.js
dashboard** at http://localhost:3000 (with `make api` running) plus voice-over. Read every
number off the screen or out of `results/metrics.json` / `results/failures.md` on recording
day. The numbers below were copied from those files on Sat Nov 14 (test period
2026-08-01 → 2026-11-14, 2529 hours).
**If `make eval` has been re-run since then, update this script before recording.**

The Gradio app (`make app`, http://127.0.0.1:7860) is the fallback if Node or the API
will not start; it shows the same window, timestamps and metrics.

---

## Pre-flight checklist (do all of it before pressing record)

- [ ] `git pull` → `make data && make train && make eval && make rank && make failures && make decision` all finish without errors
- [ ] `results/metrics.json` numbers match the ones quoted in this script (fix the script if not)
- [ ] `results/failures.md` "Why" column is filled in (no `TODO`), so the 1:15 line is true
- [ ] Terminal 1: `make api`; terminal 2: `cd web && npm install && npm run dev`
- [ ] Open http://localhost:3000 → headline shows **11 AM, 12 PM or 10 AM on Saturday**;
      the hour strip has **24 cells** with **three ranked cells** and one dashed dirtiest cell
- [ ] Click each preset (7, 3, 1.5 kWh) and check the kg sentence updates
- [ ] Click "Show the 24 hours as a table" once, then hide it again
- [ ] Browser zoom 125%, window ~1400 px wide, dark mode, bookmarks bar hidden, notifications off (Do Not Disturb)
- [ ] Close every other tab and app; no names, emails or personal info on screen
- [ ] Mic check: record 5 s, play it back
- [ ] Recorder: QuickTime → File → New Screen Recording (or ⌘⇧5), record the browser window only
- [ ] After recording: trim, check it's ≤ 2:00, upload to YouTube as **Unlisted**, paste the
      URL into `coordination/status.md` → `DEMO_VIDEO_URL`

---

## Script

### [0:00–0:15] The problem and our user

**On screen:** the GridGreen page, top of the page (title, "Historical replay" badge and
the big "Run it at …" headline).

**Say:**
> "Meet a Chicago household with a flexible load: an EV that needs a charge or a load of
> laundry. On the PJM grid, the same kilowatt-hour is dirtier at some hours than others,
> because more coal and gas are running. They can wait a few hours. The question is:
> **which hour tomorrow is cleanest?**"

### [0:15–0:50] Demo: chart, cleanest hours, modeled kg

**On screen:** the headline, the chart, the 24-cell hour strip, then the preset buttons.

**Do + say:**
1. Point at the chart.
   > "This is a historical replay of the 24 hours after our latest grid data, in grams of
   > CO₂ per kilowatt-hour — not a live forecast for tomorrow. The solid teal line is our
   > model. The dashed line is the simple baseline: tomorrow will look exactly like today."
2. Point at the headline and the ranked cells under the strip.
   > "It picks the three cleanest hours — here, **[read the three hours from the headline]** —
   > and marks them 1, 2, 3 under the strip. The dashed cell is the dirtiest hour."
3. Click **Laundry (wash + dry) 3 kWh**.
   > "Laundry, about 3 kWh: moving it from the dirtiest hour makes a modeled difference of
   > **[read kg]** kilograms of CO₂ — an average-intensity comparison, not verified real-world savings."
4. Click **EV top-up 7 kWh**.
   > "An EV top-up, 7 kWh: **[read kg]** kilograms of modeled difference, not guaranteed
   > actual savings."
   (On Nov 14's data this read 0.13 kg at 3 kWh and 0.30 kg at 7 kWh.)
5. Hover or Tab to a strip cell.
   > "Every hour has its exact number and time, and the table button shows all 24 as text."

### [0:50–1:15] How it works, with real numbers

**On screen:** scroll to "How far to trust this" (the verdict sentence and the results table).

**Say:**
> "We built this from public data: EIA's hourly grid monitor for PJM, from January 2024
> to now. We compute carbon intensity from the fuel mix and add Open-Meteo weather. The
> model is a gradient-boosted regressor trained on everything before August 1st and
> tested on August through mid-November, data it never saw.
> On that test period, our model's average error is **13.77** grams per kilowatt-hour
> against **16.94** for 'tomorrow equals today', about **19% lower**.
> But here's the honest part. When we score the decision itself, picking the three
> cleanest hours, the model gets **0.473** overlap and the baseline gets **0.483**.
> **Our numbers are more accurate, but we don't pick better hours than persistence yet.**"

### [1:15–1:30] Where it fails, and next step

**On screen:** scroll to "Where it fails" on the same page (the Oct 14 chart and paragraph).

**Say:**
> "Our worst test days, like **October 14th**, missed by about **30** grams on average —
> **[read the explanation sentence for that day]**. And on some days, like **October 20th**,
> the simple baseline actually beat us.
> Next step: test genuinely available day-ahead forecasts and independently validate on new data. Thanks for watching GridGreen!"

---

## Shot list

| # | Time | Shot | Action on screen | Notes |
|---|------|------|------------------|-------|
| 1 | 0:00–0:15 | Full page, top | Static, slow mouse over the headline | Already loaded, no spinner |
| 2 | 0:15–0:25 | Chart | Hover the teal line, then the dashed line | Legend visible |
| 3 | 0:25–0:32 | Headline + hour strip | Hover the three ranked cells | Rank numbers visible |
| 4 | 0:32–0:45 | Presets + kg sentence | Click 3 kWh, then 7 kWh; pause for the number | Wait for the text to update |
| 5 | 0:45–0:50 | One strip cell | Hover or Tab to a cell | Readout shows g/kWh and kg |
| 6 | 0:50–1:15 | "How far to trust this" | Scroll down, hover MAE, then overlap numbers | The honest sentence must be audible and visible |
| 7 | 1:15–1:27 | "Where it fails" | Hover the Oct 14 chart and paragraph | Same page, no tab switch |
| 8 | 1:27–1:30 | Back to top | End on the headline | |

## Numbers used above (source: `results/metrics.json`, `results/failures.md`)

| What | Value |
|---|---|
| Test period | 2026-08-01 → 2026-11-14, 2529 hours |
| Model MAE | 13.77 gCO₂/kWh |
| Persistence MAE | 16.94 gCO₂/kWh (model is 18.7% lower, so say "about 19%") |
| Cleanest-3-hours overlap, model | 0.473 |
| Cleanest-3-hours overlap, persistence | 0.483 |
| Worst test day | 2026-10-14: model MAE 30, persistence 36 |
| Day persistence won | 2026-10-20: model 30, persistence 26 |
