# Veritas AI Hackathon 2026 — Project Rules for Claude Code

You are the coding copilot for a 3-person high-school team in the Veritas AI International
Hackathon. Everything below is authoritative. Read it fully before every task.

## 0. Hard deadline and team facts

- **Submissions close: Sunday Nov 15, 11:59 PM ET (10:59 PM CT).** No extensions.
- Team: 3 students. AI subscriptions: Claude Pro (Claude Code), ChatGPT Plus.
- Repo: https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project
- **Track:** Climate
- **Project: GridGreen — next-day grid carbon intensity forecast for one region.**
  Who it's for: a household / school facilities manager in ONE grid region (default: the
  region the team lives in, e.g. PJM or MISO; confirm with team) deciding *when* tomorrow to
  run flexible loads (EV charging, laundry, HVAC pre-cooling, lab equipment).
  What goes in: today's hourly carbon intensity (gCO₂/kWh), generation mix, and weather
  (temperature, wind speed, solar radiation) for the region.
  What comes out: a 24-hour forecast of tomorrow's carbon intensity, the 3 cleanest hours,
  and the estimated CO₂ saved by shifting a given load (kWh) from the dirtiest to the
  cleanest hour.
- **Started from suggested project?** Our own idea (briefs §4.3.4). The structure mirrors
  §4.3.1 (next-day forecast, persistence baseline, MAE, train-earlier/test-later).
- **What we add of our own:**
  1. Our own question: does grid carbon intensity tomorrow follow a predictable daily shape,
     and is that enough for a non-expert to act on?
  2. Our own user + decision: a load-shifting recommendation with the CO₂ saved in kg, not
     just a number on a chart.
  3. Our own evaluation: besides MAE, measure **decision quality** — how often the model's
     "cleanest 3 hours" overlap with the true cleanest 3 hours on test days, vs. the
     persistence baseline ("same hours as today").
- **Data (public, cite in CREDITS.md):** primary = Electricity Maps open historical data
  (hourly carbon intensity by zone, free CSV download); alternative = US EIA Hourly Electric
  Grid Monitor (free API key) for generation mix by balancing authority, with carbon intensity
  computed from a published emissions-factor table. Weather = Open-Meteo historical API
  (no key). If the primary source isn't loading within 30 min, switch to the alternative.
- **Split:** train on all but the most recent ~3 months; test on the most recent ~3 months.
  Never shuffle hours or days.
- **Baseline:** persistence — tomorrow's hour h = today's hour h. Second baseline: same hour
  on the same weekday last week. Report MAE for both baselines and the model.
- **Model:** start with linear regression / gradient boosting (scikit-learn) on lag features
  (today's 24 hours, last week's same day) + hour-of-day + weekday + weather. No deep
  learning unless the simple model is done and measured.

## 1. Rules that can disqualify us (never violate)

1. **AI/ML must do the main job.** A website or app built with AI coding tools does not count on
   its own. Every feature must be in service of the model and its evaluation.
2. **All work happens between Sat Nov 14 12:00 AM ET and the deadline.** Never import or reuse
   code from a project the team built before the hackathon. Starter notebooks, tutorials and
   public libraries are fine.
3. **Cite everything.** Every dataset, pretrained model, tutorial, library and AI tool (including
   Claude Code and ChatGPT) goes in `CREDITS.md` with a link, the moment it is first used.
   Append to `CREDITS.md` in the same commit that introduces the dependency.
4. **Public or synthetic data only.** No real patient records, no other people's voices or
   messages, no personal information. If a dataset's license is unclear, say "check with
   organizers" — do not guess.
5. **Honest results.** Report the numbers we actually got, including weak ones. Never tune on
   the test set. If results look too good, assume leakage and investigate before reporting.
6. **The team must understand every line.** Write simple, well-commented code. Prefer
   scikit-learn / pandas over clever abstractions. When you add anything non-obvious, add a
   2–3 line comment explaining it in plain English so a student can explain it to a judge.
7. **Climate-track requirements (briefs §4.3):** focus on ONE region; train on earlier
   dates and test on later ones, never shuffle; compare with the persistence baseline
   ("tomorrow = today"); state the decision the forecast supports and who makes it. Judges
   in this track reward a fair comparison with a simple forecast, a clear prediction→decision
   link, and a test period the model never saw. Small and tied to a real place beats "the
   whole planet". (No disclaimer sentence is required for Climate.)

If a request would break any rule above, say so BEFORE doing it, then propose a compliant
alternative.

## 2. Judging criteria — tag every task with the criterion it serves

Round 1 (blind review, 100 pts) — 30% of final score:
| Criterion | Pts | What it means for our code |
|---|---|---|
| Technical execution | 30 | It runs end-to-end from a clean clone; approach is sound; tested fairly on unseen data |
| Originality | 20 | We added our own user, data or question beyond the suggested steps |
| Impact & track fit | 20 | One named user, one named moment they'd use it, inside the track's challenge |
| Testing & honesty | 15 | Baseline vs model on held-out test set; failure examples explained |
| Communication | 15 | README follows the official template; demo video ≤ 2 min |

Finals (live demo, 100 pts) — 70% of final score: Demo & clarity 30, Technical depth 30,
Impact 20, Q&A 20.

**When proposing or implementing any feature, state which criterion it serves and how many
points are at stake. If a feature serves no criterion, recommend cutting it.**

## 3. The four questions every project must answer (keep these visible in README and demo)

1. Who is it for? One specific user and the moment they'd reach for the tool.
2. What goes in, what comes out? A real input producing a real result.
3. Does it beat a simple baseline? Baseline score next to model score, same test set.
4. Where does it fail? At least one wrong prediction, with our explanation why.

## 4. Stack (decided — do not relitigate)

- **ML core (the thing judges score): Python 3.11, pandas, scikit-learn, (PyTorch / HF
  Transformers only if the chosen project needs it).** Lives in `ml/` and `notebooks/`.
- **Serving: FastAPI** in `api/` exposing `POST /predict` and `GET /health`. Loads the saved
  model from `ml/artifacts/`.
- **Demo UI: Next.js 14 (App Router) + Tailwind + shadcn/ui** in `web/`. Calls the FastAPI
  endpoint. The UI is a thin shell — never put model logic in TypeScript.
- **Fallback if behind schedule by Sunday 12:00 PM CT: drop `web/`, ship a Gradio demo in
  `ml/demo.py`.** A working Gradio demo beats a broken Next.js one.
- Hosting: Vercel for `web/`, Render/Railway/HF Spaces for `api/` — only if it works in under
  1 hour; otherwise the demo video runs everything locally and that is fine.
- Supabase: NOT used unless the project genuinely needs persisted user data. Default: no DB.

## 5. Repo layout

```
.
├── CLAUDE.md               ← this file
├── README.md               ← the official write-up (template in §7). Judges read THIS.
├── CREDITS.md              ← every dataset / model / tutorial / AI tool, with links
├── .claude/settings.json   ← Claude Code permissions + hooks
├── data/
│   ├── raw/                ← downloaded datasets (gitignored if > 50 MB; add download script)
│   └── processed/          ← cleaned splits: train.csv / val.csv / test.csv
├── ml/
│   ├── data.py             ← load + clean + split (split ONCE, save, never re-split)
│   ├── baseline.py         ← persistence (tomorrow = today) + same-hour-last-week
│   ├── features.py         ← lag features, hour/weekday, weather join
│   ├── recommend.py        ← cleanest 3 hours + CO₂ saved for a given kWh load
│   ├── train.py            ← trains model, saves to ml/artifacts/
│   ├── evaluate.py         ← prints baseline vs model on TEST set + writes results/metrics.json
│   ├── failures.py         ← dumps wrong predictions to results/failures.md
│   ├── artifacts/          ← saved model + vectorizer (gitignored if large)
│   ├── demo.py             ← Gradio fallback demo
│   └── config.py           ← REGION, SPLIT_DATE, SEED=42, thresholds, model params
├── tests/
│   ├── fixtures/sample.csv ← 100-row sample for fast tests
│   ├── test_split.py       ← no leakage, no future features
│   ├── test_baseline.py
│   └── test_api.py
├── notebooks/
│   └── 01_explore.ipynb    ← exploration only; final logic lives in ml/
├── api/
│   └── main.py             ← FastAPI: /health, /predict
├── web/                    ← Next.js demo (optional, see §4)
├── results/
│   ├── metrics.json        ← baseline + model scores, auto-written by evaluate.py
│   └── failures.md         ← failure examples, auto-written by failures.py
├── requirements.txt
└── Makefile                ← make data / train / eval / demo / api
```

## 6. Non-negotiable engineering rules

- **Split once, save, never touch test again.** `ml/data.py` writes train/val/test to
  `data/processed/`. If data has dates: train on earlier, test on later — never shuffle days.
  Use `stratify` for classification.
- **Baseline first.** `ml/baseline.py` must run and produce a number before any model is trained.
- **Right metric for the problem.** This is a forecast: report **MAE (gCO₂/kWh)** for the
  persistence baseline, the last-week baseline and the model, on the same test period. Also
  report the decision metric (overlap of predicted vs true cleanest-3-hours) and the CO₂ saved
  per kWh shifted. Break results down by weekday vs weekend and by season if the test period
  allows — that is where forecasts usually fail.
- **Everything reproducible from a clean clone:** `pip install -r requirements.txt && make data
  && make train && make eval` must work. Fix a random seed (42) everywhere.
- **Small commits, plain messages:** `feat: add TF-IDF + logistic regression baseline`. Commit
  after every working step. Never `git push --force`.
- **Never delete `data/`, `results/` or `ml/artifacts/`** without explicit team approval.
- **No secrets in git.** API keys go in `.env` (gitignored); read via `os.environ`.
- **Code must be explainable.** If you'd need more than 3 sentences to explain a function to a
  judge, simplify it.

## 7. README.md — exact official write-up template (keep these headings verbatim)

```
# Project name
**Track:** Health / Finance / Climate / Languages
**Team:** names
# The problem
Who has this problem, and why does it matter? (2-3 sentences)
# What we built
What goes in, what comes out, and how someone would use it.
# What we added
If you started from a suggested project: which one, and what you added
or changed (your own user, data or question). Otherwise, write "Our own idea".
# How it works
Data: which dataset, how many examples, how we cleaned it.
Model: what we used and why.
# Results
Our baseline scored X. Our model scored Y on held-out test data.
Where it fails, and why we think so.
# What we'd do next
One or two concrete next steps with more time.
# Sources
Datasets, pretrained models, tutorials and AI tools used, with links.
```

Whenever `results/metrics.json` or `results/failures.md` changes, offer to update the
Results section of README.md from them. Never invent numbers — copy from the files.

## 8. Demo video script (≤ 2 min, screen recording + voice)

- 0:00–0:15 The problem: who it's for, why it matters
- 0:15–1:15 The demo: real input in → result out
- 1:15–1:45 How it works: data, model, baseline vs model
- 1:45–2:00 One limitation + next step

## 9. Schedule (CT) — flag anything that doesn't fit

| By | State |
|---|---|
| Sat 1:30 PM | Track + idea chosen; data loading; `make data` works |
| Sat 6:00 PM | `make eval` prints baseline vs model on test set |
| Sat 11:00 PM | FastAPI `/predict` works; first README draft; first commit of CREDITS.md |
| Sun 12:00 PM | One measured improvement ("what we added"); demo runs start to finish. **Gradio fallback decision point.** |
| Sun 6:00 PM | README complete; failures.md written; video recorded and uploaded (unlisted) |
| Sun 8:00 PM | **First submission sent** (resubmit later as needed) |
| Sun 10:59 PM | Hard deadline |

If data isn't loading within 30 minutes of starting, recommend switching datasets. That is a
smart move, not a setback.

## 10. Engineering patterns (adapted from affaan-m/everything-claude-code)

Adopted and scaled down for a 36-hour ML build. Where a rule conflicts with §1 (hackathon
rules) or §9 (schedule), §1 and §9 win.

**Code style**
- Keep files small: 200–400 lines typical, never over 800. One concern per file
  (`ml/data.py` loads, `ml/features.py` builds features, `ml/train.py` trains, …).
- Functions under 50 lines; nesting no deeper than 4 levels. If a function is longer, split it.
- No magic numbers. Put every tunable (region, split date, seed, thresholds, model params) in
  `ml/config.py` as named constants and import from there.
- Immutability of data: functions take a DataFrame and return a new one. Never mutate the
  processed CSVs in place; `make data` is the only thing that writes `data/processed/`.
- Python: PEP 8, `black` formatting, type hints on every function, a one-line docstring on
  every public function saying what goes in and what comes out.
- Validate at boundaries: when loading a CSV or API response, assert the columns, dtypes and
  date range you expect, and fail fast with a clear message. Never silently fill or drop.
- Never swallow exceptions. If you catch, log the reason and re-raise or exit non-zero.

**Testing (right-sized)**
- Every `ml/*.py` module gets one smoke test in `tests/` that runs on a 100-row sample fixture
  in under 5 seconds. `pytest` must be green before every commit.
- Required tests, in this order of priority:
  1. `test_split_no_leakage` — max(train date) < min(test date); no overlapping timestamps.
  2. `test_baseline_runs` — persistence baseline produces a finite MAE.
  3. `test_features_no_future` — no feature column uses data from after the prediction time.
  4. `test_predict_endpoint` — `/predict` returns 24 values and the 3 cleanest hours.
- Tests-first for anything touching the split or the metrics. Fix the implementation, not the
  test, unless the test is provably wrong.
- No coverage target. Four honest tests beat forty padded ones.

**Security (the subset that matters here)**
- Before any commit, grep the diff for keys/tokens. API keys (EIA, Electricity Maps) live in
  `.env` only; read with `os.environ`, fail fast if missing.
- If a secret is ever committed: rotate it immediately, then remove it from history.
- Validate every input to `/predict` (shape, dtype, range). Return a clear 4xx, not a stack trace.

**Git workflow**
- Commit format: `<type>: <description>` with types `feat fix refactor docs test chore perf ci`.
- Commit after every green `pytest`. Never `--force`. Push with `-u` on a new branch.
- Everyone works on `main` this weekend unless a change is risky; then a short branch and a
  `/review` before merge.

**Research-first**
- Before building any non-trivial piece (data loader for an unfamiliar API, forecasting
  features), spend ≤10 minutes finding a well-maintained reference implementation, read it,
  then write our own simpler version. Cite the reference in `CREDITS.md`. Never paste a whole
  repo in — rule 2 (build during the weekend) and rule 3 (cite everything) both apply.

**Context hygiene**
- Don't start a large refactor in the last 20% of a context window. `/clear`, re-read
  CLAUDE.md + NOTES.md, then continue.
- One feature per session. Write `NOTES.md` before ending any session: what works, what's
  next, open bugs, the exact command to resume.

**Permissions**
- Use the allow-list in `.claude/settings.json`. Never run with `--dangerously-skip-permissions`.

## 11. How to work with the team

- Be concise. Lead with the deliverable. Put code in runnable files, not chat.
- Before a non-trivial feature: 3-line plan → which criterion it serves → then build.
- After a feature: run it, show the output, commit.
- When unsure whether something is allowed: say "check with organizers" (contact@veritasai.com
  — they only answer submission questions, not technical ones).
- Context is limited across 35 hours. Summarize current state at the end of long sessions in
  `NOTES.md` (what works, what's next, open bugs) so the next session can resume fast.
