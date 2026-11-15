# DATA-WEATHER — DONE (Sun Nov 15 ~11:30 CT). Next: nothing; MODEL may join fc1 columns on target_timestamp.

**Line:** DONE: 9 points x 4 vars, 25,176 hourly rows 2024-01-01 00:00 -> 2026-11-14 23:00 UTC; obs coverage 100%, fc1 95.6-98.2% (100% in test period); train-hours r(fc1, obs): temp 0.988, wind100m 0.835, solar 0.939, cloud 0.635; wind points vs PJM wind_share r=0.824 (fc1), 0.871 (obs) vs Chicago-only 0.696.

## Confirmed from the docs (read 2026-11-15) + live requests
- Previous Runs API: `https://previous-runs-api.open-meteo.com/v1/forecast`. Variables take the suffix
  `_previous_dayN` (N=1..7). Docs: "`temperature_2m_previous_day1` returns the value predicted 24 hours
  before valid time". It accepts `start_date`/`end_date`, `timezone=GMT`, `wind_speed_unit=ms` (checked with a live request).
  Model is `best_match` (the default).
- Earliest date: the docs say "most models archived from January 2024". Live check at Chicago: temp, solar
  and cloud start **2024-01-19 12:00 UTC**; wind_speed_100m starts **2024-02-16 06:00 UTC**. Hours before
  that stay empty (NaN, never 0).
- All 4 of our variables exist in Previous Runs. wind_speed_100m is stored there, so we use 100 m (the
  same height as the observed column). 80 m starts on the same date as 100 m. 10 m starts on 2024-01-19.
- Archive API: `https://archive-api.open-meteo.com/v1/archive`. Radiation is the "preceding hour mean".
  Temp, wind and cloud are instant values at the hour. So Open-Meteo hour T = EIA end-of-hour T, and we
  join on equal stamps (the same as fetch.fetch_weather()). The archive now returned data up to
  2026-11-14 23:00, so the ~5-day lag noted in CLAUDE.md did not show up today. The most recent days are
  probably model analysis, not final ERA5.
- Free tier: <10,000 calls/day, <5,000/h, <600/min, non-commercial use only. The script makes 54 calls
  (9 points x 3 years x 2 APIs) with a 3 s pause between calls, and caches every response in
  data/raw/eia_cache/weather/. A re-run on the same day makes 0 calls.
- Licence: CC BY 4.0. Attribution: "Weather data by Open-Meteo.com" with a link.

## Leakage / availability — READ THIS, MODEL
- The fc1 timestamp is the hour the forecast is FOR. Join it on `target_timestamp` (t+24), not on t.
- **availability unverified (strict T-24h rule):** previous_day1 = predicted ~24 h before the valid
  hour. The docs do not say when that model run was *published*. Runs usually appear a few hours after
  their init time, so some fc1 values were probably public only at ~T-20h, i.e. slightly after our
  forecast time t = T-24h. If MODEL needs the rule to hold strictly: set `FC_DAY = 2` in
  ml/fetch_weather_extra.py and re-run (it writes weather_fc2_points.csv, 54 new calls). Day 2 is
  48 h old, so it was certainly published before T-24h.
- Observed columns (weather_obs_points.csv) are actuals. They may be used only at time t (as x_* is
  now), never at the target hour.

## Sanity (train hours < 2026-08-01 only; data/raw/extra/weather_sanity.json)
- Forecast vs observed, mean r over 9 points: temperature 0.988, wind_speed_100m 0.835,
  shortwave_radiation 0.939, cloud_cover 0.635 (cloud is the weakest).
- Wind points track PJM wind: mean fc1 wind at il_wind/in_wind/allegheny_wind vs PJM wind_share gives
  Pearson 0.824 and Spearman 0.838. Observed wind at those points gives 0.871. Chicago-only observed
  wind (what the model uses today) gives 0.696. So the wind points DO track PJM wind, clearly better
  than Chicago alone.
