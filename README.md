# GridGreen — next-day grid carbon intensity forecast for PJM

**Track:** Climate
**Team:** [Team member 1], [Team member 2], [Team member 3]

# The problem

A school facilities manager or a household in the PJM grid region (Chicago and the
mid-Atlantic) has loads that can run at any hour: EV charging, laundry, pre-cooling a
building, lab equipment. The same kilowatt-hour emits more or less CO₂ depending on which
power plants are running at that hour. They have no simple way to know *tomorrow's* cleaner
hours tonight, when they set timers and schedules.

# What we built

GridGreen forecasts tomorrow's hourly grid carbon intensity for PJM and turns the forecast
into a decision.

- **In:** the last 24 hours of PJM carbon intensity (gCO₂/kWh), the same hour last week,
  the current fuel mix and demand, current weather at Chicago, and a load size in kWh.
- **Out:** a 24-hour forecast for tomorrow, the **3 cleanest hours** to run the load, the
  dirtiest hour to avoid, and the **kg of CO₂ saved** by moving the load from the dirtiest
  hour to the cleanest one (`ml/recommend.py`).
- **How someone uses it:** each evening they open the demo (`make app`), enter the load
  (e.g. an EV charge), and set the timer to one of the 3 suggested hours. The same forecast is
  also served by a FastAPI endpoint (`api/main.py`, `POST /predict`).

# What we added

Our own idea. Its structure follows the suggested Climate project (next-day forecast,
persistence baseline, MAE, train on earlier dates and test on later ones). What we added:

1. **Our own question and evaluation metric.** MAE alone does not tell a user when to run a
   load. We also score **cleanest-3-hours overlap**: for each test day, how many of the 3
   hours we predict as cleanest really are among the 3 cleanest (`cleanest_k_overlap()` in
   `ml/evaluate.py`). This metric matches the user's decision, and it is where we found our
   main result (see Results).
2. **An ablation built into the pipeline.** `make train` trains two models with identical
   settings (`ml/train.py`): one with all features, and one with only the carbon-intensity
   history and calendar (`lag_only_columns()` in `ml/features.py`). `make eval` scores both,
   so we can say how much fuel mix + weather actually help instead of assuming they do.
3. **Leakage discipline at the split.** Every row predicts 24 h ahead, so a training row
   dated July 31 has a target on August 1, inside the test period. `restrict_to_period()` in
   `ml/features.py` filters rows by their **target** time, not their input time. Training
   only sees targets before `SPLIT_DATE` and testing only scores targets on or after it. Fuel
   mix and weather are the values observed at forecast time. We never use tomorrow's actual
   weather, because nobody has it when the forecast is made. `tests/test_split.py` checks this.
4. **Output framed as a decision.** `ml/recommend.py` turns 24 numbers into "run it at these
   hours, save this many kg of CO₂", which is what the user actually acts on.
5. **Our own carbon-intensity series.** No free source gives PJM hourly carbon intensity
   without an account, so we compute it from EIA-930 generation by fuel (see How it works).

# How it works

**Data.**
- *Grid:* the U.S. EIA-930 Hourly Electric Grid Monitor six-month balance files, filtered to
  the PJM balancing authority. We use EIA's `(Adjusted)` net generation by fuel and demand
  columns (`ml/fetch.py`). EIA timestamps are end-of-hour UTC. Empty future hours in the
  current half-year file become missing values, never 0.
- *Carbon intensity is computed by us:* `CI = Σ(generation_by_fuel × emission_factor) /
  total_generation`, using EIA's 2023 national direct-emission factors (coal 2.31, gas 0.96,
  petroleum 2.46 lb CO₂/kWh; nuclear, hydro, wind, solar = 0; "other" treated as gas;
  storage excluded).
- *Weather:* Open-Meteo historical archive at one point, Chicago (41.88, −87.63, the ComEd
  zone of PJM): temperature, 100 m wind speed, solar radiation, cloud cover.
- *Size:* 25,176 hourly rows from 2024-01-01 to 2026-11-15 UTC in the committed
  `data/raw/gridgreen_PJM.csv`. After cleaning, the split is 22,626 train hours
  (2024-01-01 → 2026-07-31) and 2,529 test hours (2026-08-01 → 2026-11-14).
- *Cleaning (`ml/data.py`):* sort, drop duplicate hours, re-index to a complete hourly
  range, interpolate carbon-intensity gaps of ≤ 3 h, carry fuel mix/weather forward ≤ 3 h,
  drop hours still missing carbon intensity, and assert the values are in a sane range.
- *Split:* by date, once, never shuffled. Train on targets before 2026-08-01, test on
  2026-08-01 onward (summer → autumn). We never moved the split after seeing test results.

**Model.** scikit-learn `HistGradientBoostingRegressor` (`ml/train.py`, parameters in
`ml/config.py`, seed 42). For each hour *t* it predicts carbon intensity at *t* + 24 h from:
the last 24 hours of carbon intensity, the value at the same hour last week, the target's
hour / weekday / month, and fuel-mix shares, demand and weather observed at *t* (38 features).
We chose gradient boosting because it handles a few dozen tabular features, missing values
(recent weather) and non-linear hour-of-day effects with no tuning, and a student can
explain it as "many small decision trees, each fixing the last one's mistakes".

**Baselines (`ml/baseline.py`).** *Persistence:* tomorrow at hour h = today at hour h.
*Last week:* tomorrow at hour h = the same hour on the same weekday last week.

# Results

All numbers are from `results/metrics.json`: test period 2026-08-01 → 2026-11-14,
2,529 hourly forecasts, real data, never seen in training.

**Headline:** our model beats persistence on MAE but **does not** beat it on
cleanest-3-hours overlap, and overlap is the metric that matches our user's decision
(which hours to run the load). The model's numbers are closer to the truth on average, but
when you only ask "which 3 hours tomorrow are cleanest?", the simple "same as today" rule
picks them slightly more often.

| Forecast | MAE (gCO₂/kWh, lower is better) | Cleanest-3 overlap (higher is better) |
|---|---|---|
| Persistence (tomorrow = today) | 16.94 | **0.483** |
| Last week (same hour, 7 days ago) | 28.43 | 0.387 |
| **Model** (all 38 features) | **13.77** | 0.473 |
| Model, lags only (no fuel mix / weather) | 15.18 | 0.448 |
| [PENDING: results/metrics.json `model_deviation` from ml/rank.py] | [PENDING] | [PENDING] |
| [PENDING: results/metrics.json `model_rank` from ml/rank.py] | [PENDING] | [PENDING] |

- **MAE:** the model is 3.17 gCO₂/kWh better than persistence (13.77 vs 16.94, about 19%
  lower error).
- **Decision quality:** the model's predicted 3 cleanest hours overlap the true 3 cleanest
  hours 47.3% of the time, vs 48.3% for persistence. On this decision the model loses by
  about one percentage point, so we can't claim it helps the user choose hours better than
  "do what was clean today". Day by day over the 105 full test days, the model picked better
  hours than persistence on 18 days, worse on 20, and tied on 67. The bootstrap 95% interval
  for the overlap gap is −0.051 to +0.035, so the two are statistically indistinguishable on
  this decision (`results/ranking_diagnosis.json`).
- **The model gets the daily shape right more often, but not the top 3.** Correlation between
  predicted and true within-day deviation (each hour minus the day's mean) is 0.829 for the
  model vs 0.789 for persistence. The model follows the overall shape better, but that does not
  turn into picking the 3 cleanest hours more often. Our guess (not yet tested): the cleanest
  hours sit near the flat bottom of the daily curve, where errors of a few grams reorder them.
- **Ablation (do fuel mix + weather help?):** yes, a little. Adding them to the lags-only
  model lowers MAE by 1.41 gCO₂/kWh (15.18 → 13.77, about 9%) and raises overlap by 0.025
  (0.448 → 0.473). They still don't lift the model past persistence on overlap.
- **Shape-aware ranking attempts:** [PENDING: results/ranking_diagnosis.json verdict, did
  any variant beat persistence's 0.483 overlap?]

**Why persistence is so strong, and a limitation of our approach.** Our computed carbon
intensity moves in a narrow band: 228 to 488 gCO₂/kWh, mean 359, over the whole dataset
(`data/raw/gridgreen_PJM.csv`). PJM runs a lot of nuclear and gas all day, so the shape
of one day looks a lot like the next, and "same as today" is hard to beat. Part of that
narrowness comes from our method: we apply one national-average emission factor per fuel,
so every gas or coal plant counts the same whether it is an efficient new unit or an old
peaker. Real plant-by-plant emissions probably vary more by hour than our series does. The
factors are also direct (smokestack) emissions only, and one Chicago weather point stands in
for a 13-state grid.

**Where it fails.** The 5 test days with the largest model error are listed, with per-day
evidence, in [`results/failures.md`](results/failures.md). All 5 are **level offsets**: the
hourly shape was roughly right, but the whole day was shifted up or down. On each of them the
true daily average moved 18–48 gCO₂/kWh from the day before; the model covered at most 45% of
that jump and moved the wrong way on 2 of the 5 days.
- **2026-10-16 (Fri):** true daily mean fell from 414 to 366 as PJM's wind share jumped from
  3.0% to 8.4%. The model over-predicted by 26 g on average (MAE 27). Persistence did worse
  (MAE 48), but the model still covered only 45% of the drop.
- **2026-10-20 (Tue):** true daily mean rose from 354 to 380 as Chicago wind speed fell
  (5 → 2 m/s). The model under-predicted by 30 g, actually moved the wrong way, and did worse
  than persistence (MAE 30 vs 26).

**Why we think it fails:** on all 5 days PJM's wind share moved opposite to carbon intensity
(less wind, dirtier grid). Our features contain only wind observed *today*, so a change in
tomorrow's wind is invisible to the model, and our single Chicago weather point cannot see
wind or clouds elsewhere in the 13-state PJM footprint.

# What we'd do next

1. **Train directly for the decision.** Our model minimizes average error, but the user
   needs the *ranking* of hours within a day. A model that predicts each hour's deviation
   from the daily mean, or its rank within the day, targets that directly.
2. **Use weather forecasts and better emission data.** Feed tomorrow's *forecast* weather
   (a historical-forecast archive makes this leakage-free) for several PJM cities, and swap
   national emission factors for plant-level or marginal-emission data. That should widen
   the narrow 228–488 band and show the real hour-to-hour differences.

# Sources

Full list with links in [`CREDITS.md`](CREDITS.md).

- **Data:** U.S. EIA Form EIA-930 Hourly Electric Grid Monitor
  (https://www.eia.gov/electricity/gridmonitor/); EIA 2023 CO₂ emission factors per kWh
  (https://www.eia.gov/tools/faqs/faq.php?id=74); Open-Meteo Historical Weather API,
  CC BY 4.0 (https://open-meteo.com/en/docs/historical-weather-api).
- **Libraries:** scikit-learn, pandas, numpy, joblib, FastAPI, uvicorn, Gradio, pytest,
  httpx, requests, uv.
- **References read (no code copied):** PUDL EIA-930 documentation; Veritas AI Hackathon
  2026 project briefs.
- **AI tools:** Claude Code (Anthropic), used for code generation, debugging and write-up
  editing; ChatGPT Plus (OpenAI), used for [team to fill in].

---

## Run it yourself

```bash
# pip is broken on our macOS setup, so we use uv (https://docs.astral.sh/uv/)
uv venv --python 3.12
uv pip install -r requirements.txt
make data      # clean + split by date (train < 2026-08-01 <= test), from the committed CSV
make train     # train model + lags-only model → ml/artifacts/
make eval      # baselines vs models on the test set → results/metrics.json
make failures  # worst test days → results/failures.md
make app       # Gradio demo on http://127.0.0.1:7860
make api       # FastAPI on http://localhost:8000
make test      # pytest
# make fetch   # optional, needs internet: re-download EIA-930 + Open-Meteo
```
