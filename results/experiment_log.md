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
required files or columns are unavailable. No test score will be inspected until the
available steps have been selected using validation alone.
