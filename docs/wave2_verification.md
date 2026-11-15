# November 15 continuation and verification handoff

## GitHub changes performed

- Merged `DATA-GRID` via PR #1; new EIA/MISO features and EIA CO₂ cross-check
  are included in the repository, but **not selected as deployed model inputs**.
- Added `ml/decision.py`, `tests/test_decision.py`, and the measured
  `results/decision_metrics.json` output.
- Added `docs/decision_audit.md`, a `make decision` command, and README disclosure
  of retrospective evaluation, publication-time risk, and emissions-factor bias.
- Reworded Gradio and video text to identify a historical replay and avoid claiming
  measured avoided emissions.
- Updated AI credits to include ChatGPT, which helped implement this continuation.

## What was checked

- Fetched the existing `results/test_predictions.csv` directly from the
  default GitHub branch (2,529 forecasts, 105 complete UTC days).
- Independently computed post-hoc regret, daily captured fractions, and the
  fixed-seed day-bootstrap confidence interval from the CSV.
- Checked the selected branch's changed source and documentation by reading
  the files back from GitHub.
- Did **not** run `make test`, `make all`, or start Gradio in this environment:
  it does not have a Git checkout with the necessary datasets/venv and direct
  network access to clone GitHub is unavailable. The newly added tests are
  therefore **written but not executed** as of this report.

## Required human-controlled completion

1. In the actual clone run `git pull && make test && make decision && make app`.
   Check that `results/decision_metrics.json` is reproduced. If results
   change, update both README and documentation from the regenerated JSON.
2. Inspect the local Gradio page and its forecast window. Record a real
   screen-capture demonstration with the corrected
   `docs/video_script.md` and publish an unlisted video. Do not claim the
   historic replay is an operational tomorrow forecast.
3. Open the submission form and supply real teammate consent and contribution
   confirmation, school/email fields, and the published demo video URL.
   Such personal/contact and external-submission steps are intentionally
   not automated by this review.
4. Verify the official deadline, eligibility, all source/tool credits, any
   live demo link, and the complete clean-clone pipeline.
5. If adding new weather features/models later, pre-register selection on
   validation and use **new untouched test data** for confirmatory claims;
   do not choose by repeatedly evaluating the already-inspected 2026-08-01+
   test set.

## Known unresolved technical limitation

The existing model uses EIA-fuel-mix observations indexed by their reported
hour and a 24-hour forecast horizon. Those observations can be published much
later; therefore the original test performance is not yet verified as a
fully issue-time-available real-world forecast. A scientifically defensible
live system needs release-timestamp audits and real day-ahead weather archives.
