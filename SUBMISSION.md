# Submission form answers — copy-paste ready

> Deadline: **Sunday Nov 15, 11:59 PM ET**. Target your first submission for
> **8 PM CT Sunday** so there's buffer; you can resubmit freely and the latest
> version is judged.

Every number below is copied from `results/metrics.json` (test period
2026-08-01 → 2026-11-14, 2529 hourly rows, real EIA-930 data). If `make eval` is
re-run, re-copy them. Only the `[bracketed]` fields are left for a human.

---

### Project Title
GridGreen — tomorrow's cleanest hours on the PJM grid

### Your Full Name *
Santosh K. Reddy

### Your School *
[submitter's school]

### Your Email *
[submitter's email]

### Building As *
Team

### Code Link *
https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project

### Write-up Link
https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project/blob/main/README.md

### Demo Video Link
[paste YouTube unlisted link after recording]

### Track *
Climate

### One-Sentence Pitch
GridGreen studies 24-hour-ahead carbon-intensity forecasting for PJM using public grid
and weather data; the original model reduces MAE 18.7% against persistence, but
its recommended three cleanest hours do not reliably beat that simpler baseline.
The demo is a historical replay, not a verified live forecast.

### New to AI?
[answer honestly for your team]

### Rules Confirmation
☐ Verify all contributions are inside the official Nov 14–15 2026 eligibility window
   (new commits were added on Nov 15; verify the official cutoff and Git timestamps)
☑ AI/ML does the main job — a gradient-boosted regressor
   (scikit-learn HistGradientBoostingRegressor) forecasting carbon intensity
   24 hours ahead from lagged observations, fuel mix and weather observed at time t
☐ Recheck all data sources, Python dependencies and AI tools against CREDITS.md before submitting
☑ Only public data used — EIA-930 Hourly Electric Grid Monitor (US government)
   and Open-Meteo Historical Weather API (CC BY 4.0)
☑ No personal data collected
☑ Reported results are the ones we actually got (see results/metrics.json)
☐ Every team member listed contributed — a human must confirm this

### Anything Else We Should Know
Project additions we would point judges at; these are retrospective findings:

1. **Our headline result is mixed, and we say so.** On a held-out test period
   the model never saw (Aug 1 → Nov 14 2026, 2529 hours), the model beats the
   persistence baseline on error — MAE 13.77 vs 16.94 gCO₂/kWh (last-week
   baseline: 28.43). But on the metric that matches the user's actual decision —
   how many of the true 3 cleanest hours of each day it picks — it scores 0.473
   vs persistence's 0.483. Better numbers did not yet mean better decisions.
   We think the reason is that PJM's carbon intensity sits in a narrow band
   (228–488 gCO₂/kWh, mean 359), so today's daily shape is already a strong
   guide to tomorrow's. That narrow band partly comes from our method: national
   average emission factors per fuel, not plant-specific ones.
2. **An ablation, not just a baseline.** We train two models on identical
   splits — one with only lagged carbon intensity, one that adds fuel mix and
   weather. The extra features earn −1.41 MAE (15.18 → 13.77, about 9%) and
   +0.025 cleanest-3-hours overlap (0.448 → 0.473). See `ml/train.py` and the
   `model_lags_only` row in `results/metrics.json`.
3. **Leakage taken seriously.** Train on earlier dates, test on later ones,
   never shuffled. `restrict_to_period()` drops any training row whose *target*
   falls after the split date, and features only read values at or before
   time t (locked in by `tests/test_split.py`). We never feed the model
   tomorrow's actual weather, because at forecast time nobody has it.
4. **Framed as a decision, not a number.** `ml/recommend.py` turns the
   forecast into what a person acts on: the 3 cleanest hours, and the modeled kg
   difference from moving their load (in kWh) from the dirtiest to the cleanest hour.
   It is an average-intensity comparison, not verified avoided emissions.

---

## Demo entry point — how to run it

The recorded demo is the **custom Next.js dashboard** in `web/`. It reads every number
from the FastAPI service, which reads the trained model and the committed `results/`
files. Both UIs label the window as a **historical replay**, not a live forecast.

```bash
# once, after cloning
uv venv --python 3.12 && uv pip install -r requirements.txt
make data train eval rank failures decision

# terminal 1 — API on http://localhost:8000
make api

# terminal 2 — dashboard on http://localhost:3000
cd web && npm install && npm run dev
```

Production build: `cd web && npm run build && npm start`.
If the API is not on `localhost:8000`, set `NEXT_PUBLIC_API_URL` before building.

**Fallback (single process, no Node):** `make app` serves the redesigned Gradio
dashboard at http://127.0.0.1:7860. It shows the same replay window, timestamps and
held-out metrics and does not need the API server.

The page's kg figure is a **modeled average-intensity difference**, not measured or
verified avoided emissions. The API refuses to serve a next-24-hour forecast without
the trained model and says so on the page.

---

## Team details — exact spelling for certificates

| Name | Email | School |
|------|-------|--------|
| Santosh K. Reddy | [email] | [school] |
| Rithwik K. Gummadi | [email] | [school] |
| Monish K. Bandaru | [email] | [school] |

---

## Pre-submission checklist

- [ ] `make pipeline` completed end to end without errors
- [x] `make test` passes on the integrated `main` (49 tests, QA-MERGE, Nov 15)
- [x] Next.js dashboard passes `npm run lint` and `npm run build` (QA-MERGE, Nov 15)
- [x] `results/metrics.json` exists and README's numbers match it exactly
      (metrics.json exists and README now contains results; rerun and verify before submission)
- [x] README summarizes the ablation result in its results table and archived detail
- [x] README states the cleanest-3-overlap finding (model 0.473 < persistence 0.483)
- [x] At least one failure case documented with an explanation in results/failures.md
- [x] GitHub repo is public — checked Nov 14: GitHub API reports `PUBLIC`, and
      an unauthenticated request to the repo page returns HTTP 200
      (still worth one incognito look before submitting)
- [ ] Demo video opens in incognito and is under 2 minutes
- [x] `.env` is **not** in the repo — `git ls-files | grep -E '^\.env$'` printed
      nothing (Nov 14); `.env` is in `.gitignore`
- [x] No API keys in git history —
      `git log -p --all | grep -cE '(EIA_API_KEY|api_key)=[A-Za-z0-9]{20,}'` → `0`
      (rechecked after integration, Nov 15)
- [ ] Every teammate's name and email spelled right
- [x] CREDITS.md lists Claude Code and ChatGPT plus all web-stack, Python and QA tools
      used (updated Nov 15)
- [ ] Submitted before 8 PM CT Sunday; resubmit if we improve
