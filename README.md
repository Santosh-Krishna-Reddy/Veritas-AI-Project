# GridGreen — finding lower-carbon hours on the PJM grid

**Track:** Climate · **Team:** Santosh K. Reddy, Rithwik K. Gummadi, Monish K. Bandaru

# The problem

A flexible electricity load—laundry, an EV charge, or laboratory equipment—can be scheduled for different hours. PJM's generation mix changes throughout the day, so the *average direct CO₂ intensity* per kWh varies too. Can a model identify cleaner hours **24 hours ahead**, rather than simply assuming tomorrow resembles today?

# What we built

GridGreen is a reproducible Python forecasting experiment and Gradio demonstration. It estimates carbon intensity for a 24-hour target window, suggests the three lowest-intensity hours, and compares its predictions with a strong persistence baseline. **The existing demo replays a historical window from the latest processed data; it does not produce a verified live forecast for tomorrow.**

# What we added

We evaluated not only mean absolute error (MAE) but **cleanest-three overlap**, the share of recommended hours that were actually among the three lowest-intensity hours. We tested whether weather and fuel-mix features help, investigated failure days and tried alternative ranking models. A later **post-hoc** decision audit measures regret: the true intensity of selected hours minus that of the ideal three hours. The new audit was introduced after the original test was inspected, so it is exploratory.

# How it works

We derived hourly PJM intensity from U.S. EIA-930 generation by fuel, using EIA national-average **direct-emission factors**, and combined it with Open-Meteo historical weather. There are **25,176** raw hourly observations beginning January 2024. A scikit-learn gradient-boosted regressor uses intensity lags, calendar information, fuel mix, demand and Chicago weather to predict each target hour **24 hours later**. Targets before **August 1, 2026** train the original model; subsequent targets form the test set (2,529 forecasts). The split uses target timestamps, not shuffled rows.

# Results

| Forecast | Test MAE (gCO₂/kWh) ↓ | Cleanest-three overlap ↑ | Regret (gCO₂/kWh) ↓ |
|---|---:|---:|---:|
| Persistence (today → tomorrow) | 16.94 | **0.483** | 5.44 |
| Last week | 28.43 | 0.387 | 9.22 |
| Lags-only model | 15.18 | 0.448 | 5.94 |
| **Original model** | **13.77** | 0.473 | **5.12** |

The model reduces MAE by **18.7%**, but does **not** outperform persistence on cleanest-three overlap. The model's average regret is 0.32 gCO₂/kWh lower, yet the bootstrap 95% interval for model-minus-persistence regret (**−1.18 to +0.55**) crosses zero. We cannot claim a reliable improvement in the user decision. Ranking variants also failed to beat persistence. Complete figures, method and sensitivity checks: [decision audit](docs/decision_audit.md), [historical details](docs/details.md), [metrics](results/metrics.json).

**Limitations:** The backtest uses observed EIA values indexed by measurement time, even where public *release* time may be later; operational 24-hour-ahead feature availability is not verified. Model output represents rolling forecast origins, not a single fixed evening issuance. Emissions use average factors, not marginal avoided CO₂. An independent EIA comparison found our computed intensity biased **+32.97 gCO₂/kWh** on average. Three final test rows were gap-filled; the last partial day is excluded from day-based decisions. Five failure days, often involving wind shifts, are documented in [failures](results/failures.md). The demo's load-based CO₂ figure is illustrative, not verified real-world savings.

# What we'd do next

Validate input publication times, use **archived weather forecasts actually issued in advance**, and test a frozen model on genuinely new observations. Improve the emissions target using appropriate PJM-specific or marginal data before presenting real-world CO₂-saving claims.

# Sources

[EIA-930](https://www.eia.gov/electricity/gridmonitor/), [EIA emissions factors](https://www.eia.gov/tools/faqs/faq.php?id=74), [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api); all datasets, dependencies and AI-tool use are listed in [CREDITS.md](CREDITS.md).

## Run it yourself

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
make test
make data
make train
make eval
make rank
make failures
make decision
make app    # historical replay at http://127.0.0.1:7860
# make api  # FastAPI at http://localhost:8000
```

See [verification handoff](docs/wave2_verification.md) before claiming the fresh-clone pipeline is fully tested.
