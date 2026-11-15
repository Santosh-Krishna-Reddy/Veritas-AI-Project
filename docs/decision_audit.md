# Wave 2 decision audit — November 15, 2026

The original model was fit and evaluated earlier. This is an **exploratory post-hoc audit**
of the *same held-out test predictions*. We did not select or tune a new model here.
The source is `results/test_predictions.csv`; regenerate `results/decision_metrics.json`
using `python -m ml.decision`.

## What a decision costs

For each complete UTC target day and each forecast:
- Pick its three forecast-cleanest hours.
- Read the **true** intensity of those selected hours.
- Compare against the mean true intensity of the oracle's three cleanest hours.
- Regret = selected true intensity − oracle true intensity (gCO₂/kWh).
- Savings = average true intensity of the day − selected true intensity.
- Captured fraction = savings / (day average − oracle intensity), macro-averaged by day.

| Forecast | Test MAE (gCO₂/kWh) | Three-hour overlap | Mean regret (gCO₂/kWh) | Mean possible-savings fraction captured |
|---|---:|---:|---:|---:|
| Model | 13.77 | 0.473 | 5.12 | 79.0% |
| Persistence | 16.94 | 0.483 | 5.44 | 78.6% |
| Last week | 28.43 | 0.387 | 9.22 | 67.3% |
| Lags only | 15.18 | 0.448 | 5.94 | 75.4% |

Across **105 complete UTC days**, model-minus-persistence regret averages **−0.316 gCO₂/kWh**,
but the **day-bootstrap 95% interval is approximately −1.18 to +0.55 gCO₂/kWh**.
This interval includes zero. The data do **not** demonstrate an improvement in the
user's hour-picking decision. Report the original overlap as well; regret was added
*after* inspecting first test results, not as a pre-registered primary outcome.

For context, the median true intensity difference between the third- and sixth-cleanest
hours of each day is **7.01 gCO₂/kWh** (10th–90th percentile: **2.76–14.12**).
This supports investigating flat-bottom ambiguity, but does not prove that it causes
the model's ranking errors.

The generated JSON also includes sensitivity to UTC vs Chicago calendar days and
k = 1, 3, 6 cleanest hours. Do not selectively report whichever version looks best.

## Critical deployment and leakage limits

1. **These are rolling 24-hour-ahead backtests.** Every target hour comes from a
   different forecast origin, exactly 24 hours earlier. They are *not* one fixed
   daily forecast issued at, for example, 8 PM the previous night.
2. **Observation-time is not publication-time.** EIA-930's fuel-mix and adjusted
   generation columns are often published the next morning. A feature recorded at
   model-origin time `t` may not actually have been available at `t`.
   The current backtest does not prove operationally available inputs; it should
   be presented as retrospective research rather than deployable day-ahead prediction.
3. **The demo is a replay tied to data on disk.** Without refreshing the dataset and
   verifying data availability, the last model-issued forecast is not necessarily
   tomorrow relative to the current date. The Gradio UI identifies its real timestamps.
4. **Intensity is an approximation, not measured household emissions.** It applies
   national-average direct-emissions factors to generation by fuel, not PJM's actual
   marginal emissions. Operational savings depend on marginal dispatch, grid dynamics,
   whether the load is genuinely shifted, and other assumptions.
5. **Independent benchmark comparison.** The separate exploratory EIA comparison
   in `results/ci_crosscheck.json` on pre-August 2026 hours found correlation 0.985
   but **+32.97 gCO₂/kWh average bias** (our computed series minus EIA's).
   Do not call this a calibrated emissions measurement.
6. **The test set has already been examined.** Any subsequent feature search or
   model selection must use a separate validation period and a genuinely new,
   untouched test set for confirmatory claims.
7. **Data currency and timezone.** The replay labels America/Chicago, but the target
   series and primary daily metrics use UTC. Daylight saving changes local day length.

## Reproduction

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
.venv/bin/python -m ml.decision
.venv/bin/python -m pytest -q tests/test_decision.py
```

Results in this document were calculated directly from the committed test prediction
CSV. This is **not** a declaration that the above commands or the full project tests
have been executed on a fresh clone in this review.
