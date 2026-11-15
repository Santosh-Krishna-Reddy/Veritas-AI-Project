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
[submitter's full name]

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
GridGreen forecasts tomorrow's hourly carbon intensity on the PJM grid and tells a
household or school facilities manager the 3 cleanest hours to run flexible loads
like laundry or EV charging — our model cuts forecast error 18.7% versus
"tomorrow = today" (MAE 13.77 vs 16.94 gCO₂/kWh), yet still picks the true
cleanest 3 hours slightly less often than that simple baseline (47.3% vs 48.3%),
and we report both.

### New to AI?
[answer honestly for your team]

### Rules Confirmation
☑ All work done between 12:00 AM ET Nov 14 and 11:59 PM ET Nov 15
   (every commit in the repo is dated Nov 14 2026)
☑ AI/ML does the main job — a gradient-boosted regressor
   (scikit-learn HistGradientBoostingRegressor) forecasting carbon intensity
   24 hours ahead from lagged observations, fuel mix and weather observed at time t
☐ Every dataset, library, tutorial and AI tool credited in CREDITS.md
   — NOT YET TRUE: see URGENT entry in coordination/blockers.md
☑ Only public data used — EIA-930 Hourly Electric Grid Monitor (US government)
   and Open-Meteo Historical Weather API (CC BY 4.0)
☑ No personal data collected
☑ Reported results are the ones we actually got (see results/metrics.json)
☐ Every team member listed contributed — a human must confirm this

### Anything Else We Should Know
Our own idea, not a suggested project. Four things we'd point judges at:

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
   forecast into what a person acts on: the 3 cleanest hours, and the kg of
   CO₂ saved by moving their load (in kWh) from the dirtiest to the cleanest hour.

---

## Team details — exact spelling for certificates

| Name | Email | School |
|------|-------|--------|
| [member 1 full name] | [email] | [school] |
| [member 2 full name] | [email] | [school] |
| [member 3 full name] | [email] | [school] |

---

## Pre-submission checklist

- [ ] `make pipeline` completed end to end without errors
- [ ] `results/metrics.json` exists and README's numbers match it exactly
      (metrics.json exists; README Results section is still the empty template as of Nov 14)
- [ ] README states the ablation result (what weather + fuel mix actually added)
- [ ] README states the cleanest-3-overlap finding (model 0.473 < persistence 0.483)
- [ ] At least one failure case documented with our explanation
      (results/failures.md lists 5 days; every "Why" is still TODO)
- [x] GitHub repo is public — checked Nov 14: GitHub API reports `PUBLIC`, and
      an unauthenticated request to the repo page returns HTTP 200
      (still worth one incognito look before submitting)
- [ ] Demo video opens in incognito and is under 2 minutes
- [x] `.env` is **not** in the repo — `git ls-files | grep -E '^\.env$'` printed
      nothing (Nov 14); `.env` is in `.gitignore`
- [x] No API keys in git history —
      `git log -p --all | grep -cE '(EIA_API_KEY|api_key)=[A-Za-z0-9]{20,}'` → `0` (Nov 14)
- [ ] Every teammate's name and email spelled right
- [ ] CREDITS.md lists Claude and ChatGPT (required by the rules)
      (both listed; ChatGPT's "used for" is still a placeholder)
- [ ] Submitted before 8 PM CT Sunday; resubmit if we improve
