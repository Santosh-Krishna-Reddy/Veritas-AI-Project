# Locked facts and file ownership — read this before you touch anything

## Project
GridGreen — next-24h grid carbon intensity forecast for PJM (Chicago / mid-Atlantic).
Veritas AI International High School Hackathon 2026, **Climate** track.
Deadline: Sun Nov 15, 11:59 PM ET. Target first submission: **8 PM CT Sunday**.
Repo: https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project

## Environment — do not try to "fix" this
- Homebrew pip on this machine is BROKEN (vendored truststore crashes on macOS 26
  because platform.mac_ver() returns ""). Affects python3.12 and 3.14 alike.
- We use `uv` instead. Venv lives at `.venv`, built with `uv venv --python 3.12`.
- The Makefile calls `.venv/bin/python` directly — never `python` or `python3`.
- To add a package: `uv pip install <name>` then add it to requirements.txt.
- NEVER run `pip install`, `python3 -m venv`, or `--break-system-packages`. They fail.

## Measured results as of the first real-data run (results/metrics.json)
Test period 2026-08-01 → 2026-11-14, 2529 rows, data_source "real".

| model            | MAE   | cleanest_3_overlap |
|------------------|-------|--------------------|
| persistence      | 16.94 | 0.483              |
| last_week        | 28.43 | 0.387              |
| model (38 feats) | 13.77 | 0.473              |
| model_lags_only  | 15.18 | 0.448              |

**THE CENTRAL FINDING:** the model wins on MAE (−19% vs persistence) but does NOT
beat persistence on cleanest_3_overlap — the metric that matches the actual user
decision. Every write-up, README section and video line must state this honestly.
Do not bury it, do not round it away, do not report only MAE.

The ablation IS a win: weather + fuel mix earn −1.41 MAE (9%) and +0.025 overlap.

Observed carbon intensity range is narrow (228–488, mean 359), which is why
persistence is a strong baseline. State this as a limitation of our
emission-factor approach, not as a bug.

## File ownership — write ONLY inside your own paths
- RANKING  : ml/rank.py (new), ml/evaluate.py, results/**
- FAILURES : ml/failures.py, results/failures.md
- WRITEUP  : README.md, CREDITS.md
- DEMO     : app.py, docs/video_script.md
- SUBMIT   : SUBMISSION.md
- QA       : coordination/qa_report.md only (plus reporting to the human)

Shared, read-only to everyone: ml/config.py, ml/features.py, ml/data.py,
ml/fetch.py, ml/train.py, api/main.py, tests/**.
If you believe a shared file must change, write the proposal into
coordination/blockers.md and let QA raise it with the human. Do not edit it.

## Rules that constrain all work (from the hackathon briefs)
- All work must date from Nov 14-15 2026. Nothing pre-existing.
- Every dataset, model, tutorial and AI tool must be credited with a link.
- Reported numbers must be the ones we actually got. No estimates, no rounding up.
- Results must come from test data the model never saw. Never touch the split.
- Public/synthetic data only.
