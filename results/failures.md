# Where the model fails (PJM (Chicago / mid-Atlantic grid))

The 5 test days (UTC) with the highest model MAE, in gCO2/kWh. Auto-written by `make failures` from `results/test_predictions.csv` and `data/processed/`; per-feature numbers are in `results/failure_features.csv`. 'Level offset' = the mean error (bias) is bigger than the within-day spread of the error.

| Day | Weekday | Model MAE | Persistence MAE | Avg true gCO2/kWh | Error type | Why |
|---|---|---|---|---|---|---|
| 2026-10-14 | Wed | 30 | 36 | 411 | level offset | -30 g all day; temp_c 24 -> 19 (1.02x test avg); wind_share 6.4% -> 3.3% (1.16x test avg) |
| 2026-09-16 | Wed | 30 | 43 | 377 | level offset | -30 g all day; wind_share 4.6% -> 1.3% (0.47x test avg); demand_mw 95174 -> 103761 (1.06x test avg) |
| 2026-10-20 | Tue | 30 | 26 | 380 | level offset | -30 g all day; wind_ms 5 -> 2 (0.39x test avg); cloud_pct 0 -> 38 (0.67x test avg) |
| 2026-10-16 | Fri | 27 | 48 | 366 | level offset | +26 g all day; wind_share 3.0% -> 8.4% (2.98x test avg); wind_ms 6 -> 9 (1.82x test avg) |
| 2026-10-11 | Sun | 27 | 25 | 364 | level offset | -25 g all day; wind_ms 7 -> 4 (0.82x test avg); wind_share 6.4% -> 4.6% (1.61x test avg) |

**2026-10-14 (Wednesday).** Level offset: under-predicted by 30 g on average (within-day spread 12 g). True daily mean went 375 -> 411 (+36) vs the day before; the model moved only 17% of that gap. Biggest day-over-day changes in possible causes: temp_c 24 -> 19 (1.02x test avg); wind_share 6.4% -> 3.3% (1.16x test avg).

**2026-09-16 (Wednesday).** Level offset: under-predicted by 30 g on average (within-day spread 16 g). True daily mean went 334 -> 377 (+43) vs the day before; the model moved only 32% of that gap. Biggest day-over-day changes in possible causes: wind_share 4.6% -> 1.3% (0.47x test avg); demand_mw 95174 -> 103761 (1.06x test avg).

**2026-10-20 (Tuesday).** Level offset: under-predicted by 30 g on average (within-day spread 14 g). True daily mean went 354 -> 380 (+26) vs the day before; the model moved the wrong way (-15% of the gap). Biggest day-over-day changes in possible causes: wind_ms 5 -> 2 (0.39x test avg); cloud_pct 0 -> 38 (0.67x test avg).

**2026-10-16 (Friday).** Level offset: over-predicted by 26 g on average (within-day spread 14 g). True daily mean went 414 -> 366 (-48) vs the day before; the model moved only 45% of that gap. Biggest day-over-day changes in possible causes: wind_share 3.0% -> 8.4% (2.98x test avg); wind_ms 6 -> 9 (1.82x test avg).

**2026-10-11 (Sunday).** Level offset: under-predicted by 25 g on average (within-day spread 23 g). True daily mean went 346 -> 364 (+18) vs the day before; the model moved the wrong way (-36% of the gap). Biggest day-over-day changes in possible causes: wind_ms 7 -> 4 (0.82x test avg); wind_share 6.4% -> 4.6% (1.61x test avg).

**Pattern.** 5 of 5 days are level offsets (the whole day shifted up or down, the hourly shape roughly right). On every day the true average moved by 18-48 g from the day before. The model, which forecasts from yesterday's lags and yesterday's weather, covered at most 45% of that jump and moved the wrong way on 2. On 5 of 5 days PJM's wind share moved opposite to carbon intensity (wind down -> dirtier, wind up -> cleaner). Our features only contain wind observed today, so a wind change tomorrow is invisible to the model. The fix is a weather FORECAST feature (wind/solar for the target day); our single Chicago weather point also cannot see wind or clouds elsewhere in the 13-state PJM footprint.
