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
