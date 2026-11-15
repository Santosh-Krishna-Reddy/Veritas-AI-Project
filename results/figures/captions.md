# Figure captions

Auto-written by `python -m ml.figures`; every number comes from results/decision_metrics.json.

- **01_week.png**: In the week around 2026-10-14, the model's worst test day, it missed by 29.9 gCO₂/kWh on average, against 36.1 for persistence.
- **02_shape.png**: Averaged over all data (2024-01-01 to 2026-11-15), PJM is cleanest around 12:00 and dirtiest around 21:00 Chicago time, with an average daily swing of 38.1 gCO₂/kWh between the cleanest and dirtiest hour of a month.
- **03_scoreboard.png**: MAE: model 13.77 vs persistence 16.94 gCO₂/kWh; share of possible saving captured: model 82.5% vs persistence 81.5%; model minus persistence regret -0.32 g/kWh (95% bootstrap CI -1.20 to +0.52, within noise).
- **04_when_wrong.png**: The model's weekday MAE peaks at 9:00 Chicago time (16.6 gCO₂/kWh) and its weekend MAE at 10:00 (17.9).
- **05_wind.png**: Across 105 test days, the day-over-day change in PJM wind share correlates with the model's daily bias at r = 0.49 (persistence r = 0.58): when tomorrow is windier, the forecast is too high.
- **06_flat_bottom.png**: On a median test day the 3rd and 6th cleanest hours differ by 7.0 gCO₂/kWh (10th–90th percentile 2.8–14.1, 105 days), smaller than the model's 13.8 gCO₂/kWh MAE, so small errors reorder the cleanest hours while costing the user little (model regret 5.1 g/kWh).
