# MODEL experiment log

## Pre-registered plan — 2026-11-15 before ladder training

The validation targets are 2026-05-01 through 2026-07-31. Each validation model is
fitted only on targets before 2026-05-01. After selecting a step, each available step
is refitted on all training targets before the fixed 2026-08-01 split and scored once
on the held-out test period.

The feature ladder is fixed in advance:

- G0: carbon-intensity lags plus target calendar features (`model_lags_only`).
- G1: G0 plus fuel mix and Chicago weather observed at forecast time (`model`).
- G2: G1 plus target-day US federal holiday/weekend flags and Chicago local hour.
- G3: G2 plus grid extras observed at forecast time: interchange, MISO fuel shares,
  and MISO demand.
- G4: G3 plus observed multi-point weather aggregates at forecast time.
- G5: G4 plus target-hour day-ahead weather forecasts and forecast-minus-observed
  deltas.
- G6: G5 plus PJM target-hour day-ahead demand forecast; availability is unverified,
  so G6 can be scored but can never be selected.

Selection rule: "final = the step with the lowest validation MAE; within 0.2 g/kWh,
prefer fewer features".

At pre-registration time, `data/raw/extra/` is absent. G0, G1, and G2 will always run.
G3–G6 will be checked individually and recorded as `skipped: file missing` when their
required files or columns are unavailable. The repository already contains published
G0/G1 test metrics, and an earlier validation run printed them; they will not inform
selection. The available ladder will be selected using validation alone, then the full
available ladder will be scored together once after selection.

## Locked outcome — 2026-11-15

Validation MAE was G0 15.820, G1 14.752, and G2 14.843 g/kWh. G1 was selected before
the ladder's held-out scoring pass because G2 was within 0.2 g/kWh and G1 has fewer
features. Test MAE was G0 15.181, G1 13.768, and G2 13.729; cleanest-3 overlap was
0.448, 0.473, and 0.479 respectively. G2's test result did not change the pre-registered
selection. G3–G6 were skipped because `data/raw/extra/` and their required files were
missing. The core ladder and validation finished before the human's 5:45 PM cutoff, so
the optional central 80% quantile band and `ml/predict.py` were then completed. Actual
test coverage is 0.697509 (69.75%), below the 80% target; no tuning followed this result.
