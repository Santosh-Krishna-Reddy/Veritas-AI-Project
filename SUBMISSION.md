# Submission form answers — copy-paste ready

> Deadline: **Sunday Nov 15, 11:59 PM ET**. Target your first submission for
> **8 PM CT Sunday** so there's buffer; you can resubmit freely and the latest
> version is judged.

Fill in every `[bracketed]` placeholder. Numbers marked `<from results/>` must be
copied from `results/metrics.json` after `make eval` — **never estimated**.

---

### Project Title
GridGreen — the cleanest hour to run your flexible loads

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
GridGreen forecasts the next 24 hours of grid carbon intensity for the PJM grid
and tells a Chicago household the single cleanest hour to run their laundry,
dishwasher or EV charger — cutting the carbon cost of a chore they were doing
anyway, with no equipment and no money spent.

### New to AI?
[answer honestly for your team]

### Rules Confirmation
☑ All work done between 12:00 AM ET Nov 14 and 11:59 PM ET Nov 15
☑ AI/ML does the main job — a gradient-boosted regressor forecasting carbon
   intensity 24 hours ahead from lagged observations, fuel mix and weather
☑ Every dataset, library, tutorial and AI tool credited in CREDITS.md
☑ Only public data used — EIA-930 Hourly Grid Monitor and Open-Meteo, both public
☑ No personal data collected
☑ Reported results are the ones we actually got (see results/metrics.json)
☑ Every team member listed contributed

### Anything Else We Should Know
Our own idea, not a suggested project. Three things we'd point judges at:

1. **An ablation, not just a baseline.** We train two models on identical splits
   — one with only lagged carbon intensity, one that adds fuel mix and weather —
   so we can report exactly how much the extra features earn rather than
   asserting they help. See `ml/train.py` and the `model_lags_only` artifact.
2. **Leakage taken seriously.** `restrict_to_period()` drops any training row
   whose *target* falls after the split date, and features only ever read values
   at or before time t. We never feed the model tomorrow's actual weather,
   because at forecast time nobody has it.
3. **Framed as a decision, not a number.** `ml/recommend.py` converts the
   forecast into the thing a person actually acts on: which hour, and how many
   kg of CO₂ that choice saves for their specific load.

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
- [ ] README states the ablation result (what weather + fuel mix actually added)
- [ ] At least one failure case documented with our explanation
- [ ] GitHub repo opens in an incognito window without signing in
- [ ] Demo video opens in incognito and is under 2 minutes
- [ ] `.env` is **not** in the repo (`git ls-files | grep -c '^\.env$'` returns 0)
- [ ] Every teammate's name and email spelled right
- [ ] CREDITS.md lists Claude and ChatGPT (required by the rules)
- [ ] Submitted before 8 PM CT Sunday; resubmit if we improve
