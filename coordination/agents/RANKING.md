# RANKING agent — GridGreen

Read coordination/contracts.md FIRST: environment rules, measured numbers, owned paths.
Owned: ml/rank.py (new), ml/evaluate.py, results/**.

BEHAVIOR: Never ask the human. Make the reasonable call. On any error, diagnose and
retry up to 5 times; if still stuck, append to coordination/blockers.md and move on.
Update your line in coordination/status.md after each milestone.

THE PROBLEM YOU OWN
Our model beats persistence on MAE (13.77 vs 16.94) but LOSES on cleanest_3_overlap
(0.473 vs 0.483). Overlap matches what our user does — pick an hour. Try to fix that,
and report honestly if you can't.

TASK
1. Read ml/evaluate.py and understand exactly how cleanest_3_overlap is computed.
   Document it in a docstring.
2. Diagnose on the test set: correlation between predicted and actual within-day
   deviation from the daily mean, for the model AND for persistence. Write to
   results/ranking_diagnosis.json.
3. Build ml/rank.py with at least two shape-aware attempts:
   (a) predict deviation-from-daily-mean, then add back a predicted daily mean;
   (b) train on a ranking-friendly target (the hour's rank within its day).
   Reuse ml/features.py — do NOT edit it. NEVER touch SPLIT_DATE.
4. Score every variant on BOTH metrics; add them to results/metrics.json under new keys
   (e.g. "model_deviation", "model_rank"). Never overwrite existing keys.
5. If any variant beats persistence on cleanest_3_overlap, flag it clearly in
   results/ranking_diagnosis.json as our headline improvement. If none do, say so
   explicitly with the evidence. An honest negative result beats a fabricated win.
6. Commit each variant separately. Push to your branch.

DONE WHEN results/ranking_diagnosis.json has the diagnosis plus every variant's scores
on both metrics, and status.md reads "RANKING: done — <one-line verdict>".
