# Blockers

Agents append here when stuck after 5 honest attempts. QA reads this file and
relays to the human. Never delete another agent's entry; add a resolution line
underneath it instead.

Format:
    ## [AGENT] 2026-11-14T19:05Z
    What I was doing:
    What blocked me (exact error / what I could not reach):
    What I need from the human:
    What I did instead while waiting:

---

## [RANKING] 2026-11-14
What I was doing: wiring ml/rank.py into the pipeline.
What blocked me: Makefile and tests/** are shared/read-only, so I could not add a `rank` target or a smoke test.
What I need from the human: (1) add `rank: ; $(PY) -m ml.rank` to the Makefile and append `rank` to `all` after `eval`;
  (2) optionally a smoke test for ml/rank.py (CLAUDE.md §10 wants one per ml/*.py module).
What I did instead: evaluate.py now keeps keys it doesn't own in metrics.json, so `make eval` no longer wipes
  model_deviation / model_deviation_today_mean / model_rank. Re-run `.venv/bin/python -m ml.rank` after any retrain.

## [SUBMIT] 2026-11-14 — URGENT
What I was doing: checking each Rules Confirmation line in SUBMISSION.md against the repo.
What blocked me: two lines can't honestly be ticked yet.
  1. "Every dataset, library, tutorial and AI tool credited in CREDITS.md" is FALSE today.
     requirements.txt uses numpy, joblib, uvicorn, pydantic, gradio, pytest, httpx; none of
     them are in CREDITS.md. The uv installer (used by the Makefile) is missing too. ChatGPT's
     "used for:" is still a placeholder. Owner: WRITEUP (CREDITS.md).
  2. "Every team member listed contributed": only a human can confirm this.
What I need from the human: WRITEUP fixes CREDITS.md (or a human does). A human confirms
  line 2 and fills the human-only fields: submitter name/school/email, 3 team rows,
  "New to AI?", demo video URL.
What I did instead while waiting: left both boxes unticked (☐) with a note. Once CREDITS.md is
  fixed, tick line 1 in SUBMISSION.md. Also noted for WRITEUP/FAILURES: the README is still the
  blank template (the Write-up Link points at it), and every "Why" in results/failures.md is TODO.
Security: clean. No .env tracked, 0 key-shaped strings in git history. The repo is PUBLIC
  (gh API + unauthenticated HTTP 200).

## [DEMO] 2026-11-15T04:45Z
What I was doing: verifying `make app` forecasts.
What blocked me: two issues in files DEMO does not own. Not blocking the demo.
  1. ml/data.py (shared): the last 3 rows of data/processed/test.csv (2026-11-14 06:00–08:00 UTC)
     are exact copies of 05:00 (CI 373.89, demand 90893). Looks like trailing-gap filling at the end
     of the series. That makes the tail of the app's persistence line flat (Sun 12–2 AM).
     Proposal: drop trailing gap hours instead of filling them.
  2. requirements.txt (unowned): says `gradio>=4.0`, but app.py needs Gradio 6 (`launch(theme=)`;
     `overlay_point` was removed in 6). Proposal: change it to `gradio>=6.0`.
What I need from the human: approve or reject both proposals.
What I did instead: app.py works with the installed Gradio 6.32.0; hf_space_deploy.md pins sdk_version 6.32.0.
Resolution (ml/data.py proposal): REJECTED for this submission: 3/2529 test rows affected; to be disclosed as a limitation in README.
