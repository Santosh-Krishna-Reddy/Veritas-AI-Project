# FAILURES agent — GridGreen

Read coordination/contracts.md FIRST. Owned: ml/failures.py, results/failures.md.

BEHAVIOR: Never ask the human. Retry 5x on errors, then log to
coordination/blockers.md and continue. Update your status.md line.

THE PROBLEM
`make failures` lists the five worst test days with "TODO" in the Why column.
Judges award 15 points for knowing where the model fails; TODOs score zero.
Days: 2026-10-14 (Wed), 2026-09-16 (Wed), 2026-10-20 (Tue), 2026-10-16 (Fri), 2026-10-11 (Sun).

TASK
1. For each day, compare features in data/processed/test.csv against the test-set
   average: wind_ms, solar_wm2, cloud_pct, temp_c, demand_mw, each fuel share.
   Was the model's error a level offset or a within-day shape error?
   Write results/failure_features.csv.
2. Write a specific, numbers-backed hypothesis per day. "Wind was 2.3x the test
   average and the model under-predicted the drop" is an explanation.
   "Unusual conditions" is not.
3. Optional: web-search for storms, holidays or outages on those dates. If web access
   is blocked, log it and explain from the data alone — that is sufficient.
4. Rewrite ml/failures.py so the Why column is generated from the feature comparison,
   not hardcoded.
5. Write results/failures.md: the table, one paragraph per day, and a closing
   paragraph on the pattern across all five (or say there is none).

DONE WHEN zero TODOs remain and status.md reads "FAILURES: done".
