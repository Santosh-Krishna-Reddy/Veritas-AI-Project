"""Download extra weather for GridGreen: several PJM points, observed AND day-ahead forecast.

Why: one Chicago point cannot see a 13-state grid, and the input the model is missing is
tomorrow's weather. Open-Meteo keeps the forecasts it issued in the past ("Previous Runs
API"), so we can use the forecast that existed a day ahead without leaking the actual.

Sources (free, no key, CC BY 4.0, see coordination/credits.d/DATA-WEATHER.md):
  observed : https://archive-api.open-meteo.com/v1/archive            (reanalysis)
  forecast : https://previous-runs-api.open-meteo.com/v1/forecast     (`<var>_previous_day1`
             = the value predicted 24 hours before the hour it is for)

Run:  .venv/bin/python -m ml.fetch_weather_extra
Out:  data/raw/extra/weather_obs_points.csv  columns <point>_<var>
      data/raw/extra/weather_fc1_points.csv  columns <point>_<var>_fc1
      data/raw/extra/weather_sanity.json     forecast-vs-observed checks (train hours only)

Timestamps: we ask for timezone=GMT, so `time` is UTC, parsed exactly like
fetch.fetch_weather(). Open-Meteo labels hour T with the instant value at T (temperature,
wind, cloud) and with the mean over the preceding hour (T-1h, T] for radiation. EIA stamps
are END of hour, so EIA hour T and Open-Meteo hour T line up and we join on equal stamps.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from ml import config as C

# Edit freely: name -> (lat, lon). Load centres first, then rough wind-farm areas.
POINTS = {
    "chicago": (41.88, -87.63),
    "columbus": (39.96, -83.00),
    "pittsburgh": (40.44, -80.00),
    "philadelphia": (39.95, -75.17),
    "washington": (38.91, -77.04),
    "richmond": (37.54, -77.44),
    "il_wind": (40.9, -88.6),
    "in_wind": (40.6, -87.3),
    "allegheny_wind": (39.9, -79.1),
}
WIND_POINTS = ["il_wind", "in_wind", "allegheny_wind"]
# Same variables as config.WEATHER_VARS. wind_speed_100m IS stored by the Previous Runs API
# (checked live 2026-11-15; available from 2024-02-16, the others from 2024-01-19).
VARS = ["temperature_2m", "wind_speed_100m", "shortwave_radiation", "cloud_cover"]
FC_DAY = 1  # 1 = forecast made 24 h before the hour; 2 = 48 h before (strictly older)

START = date(2024, 1, 1)
ARCHIVE_URL = C.OPEN_METEO_URL
PREVIOUS_RUNS_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
CACHE_DIR = C.EIA_CACHE_DIR / "weather"
OUT_DIR = C.RAW_DIR / "extra"
OBS_CSV = OUT_DIR / "weather_obs_points.csv"
FC_CSV = OUT_DIR / f"weather_fc{FC_DAY}_points.csv"
SANITY_JSON = OUT_DIR / "weather_sanity.json"
SLEEP_S = 3        # pause between live calls (free tier: 600 calls/min, 5000/h, 10000/day)
RETRIES = 5
# Physically sane ranges per variable; anything outside means a parsing or unit bug.
RANGES = {"temperature_2m": (-45, 50), "wind_speed_100m": (0, 60),
          "shortwave_radiation": (0, 1400), "cloud_cover": (0, 100)}


def get_json(url: str, params: dict, cache: Path) -> dict:
    """GET a JSON response, or read it from the cache file if we already have it.
    Retries on rate limits / server errors with a growing pause, then exits non-zero."""
    if cache.exists():
        return json.loads(cache.read_text())
    for attempt in range(1, RETRIES + 1):
        r = requests.get(url, params=params, timeout=180)
        if r.status_code == 200:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(r.text)
            time.sleep(SLEEP_S)
            return r.json()
        print(f"  attempt {attempt}: HTTP {r.status_code} {r.text[:200]}")
        if r.status_code != 429 and r.status_code < 500:
            break                      # a 4xx other than rate limit will not fix itself
        time.sleep(SLEEP_S * 10 * attempt)
    sys.exit(f"Open-Meteo failed for {url} {params}")


def year_ranges(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into calendar-year pieces: one API call per year."""
    out = []
    for year in range(start.year, end.year + 1):
        out.append((max(start, date(year, 1, 1)), min(end, date(year, 12, 31))))
    return out


def to_frame(js: dict, point: str, api_suffix: str, col_suffix: str) -> pd.DataFrame:
    """One Open-Meteo JSON response -> frame with `timestamp` + `<point>_<var><col_suffix>`."""
    hourly = js.get("hourly")
    if not hourly or "time" not in hourly:
        sys.exit(f"Open-Meteo response for {point} has no hourly data: {str(js)[:300]}")
    missing = [v for v in VARS if v + api_suffix not in hourly]
    if missing:
        sys.exit(f"Open-Meteo response for {point} lacks {missing}")
    df = pd.DataFrame({f"{point}_{v}{col_suffix}": hourly[v + api_suffix] for v in VARS},
                      dtype="float64")
    df.insert(0, C.TS_COL, pd.to_datetime(hourly["time"], utc=True))
    return df


def fetch_points(kind: str, start: date, end: date) -> pd.DataFrame:
    """kind 'obs' (archive) or 'fc' (previous runs). Returns one row per UTC hour, all points."""
    url = ARCHIVE_URL if kind == "obs" else PREVIOUS_RUNS_URL
    api_suffix = "" if kind == "obs" else f"_previous_day{FC_DAY}"
    col_suffix = "" if kind == "obs" else f"_fc{FC_DAY}"
    hours = pd.date_range(pd.Timestamp(start, tz="UTC"),
                          pd.Timestamp(end, tz="UTC") + pd.Timedelta(hours=23), freq="h")
    out = pd.DataFrame({C.TS_COL: hours})
    for point, (lat, lon) in POINTS.items():
        pieces = []
        for a, b in year_ranges(start, end):
            # The end date is in the cache name, so a finished year is fetched once and a
            # re-run on the same day costs no API calls at all.
            cache = CACHE_DIR / f"{kind}{FC_DAY if kind == 'fc' else ''}_{point}_{a}_{b}.json"
            print(f"{kind} {point} {a} -> {b}{'  (cached)' if cache.exists() else ''}")
            params = {"latitude": lat, "longitude": lon, "start_date": a.isoformat(),
                      "end_date": b.isoformat(), "hourly": ",".join(v + api_suffix for v in VARS),
                      "timezone": "GMT", "wind_speed_unit": "ms"}
            pieces.append(to_frame(get_json(url, params, cache), point, api_suffix, col_suffix))
        one = pd.concat(pieces).drop_duplicates(C.TS_COL)
        out = out.merge(one, on=C.TS_COL, how="left")   # hours the API lacks stay empty
    return out


def validate(df: pd.DataFrame, name: str) -> dict:
    """Fail fast on duplicate / gappy timestamps or out-of-range values; return coverage."""
    ts = df[C.TS_COL]
    assert ts.is_unique, f"{name}: duplicate timestamps"
    assert (ts.diff().dropna() == pd.Timedelta(hours=1)).all(), f"{name}: not strictly hourly"
    for col in df.columns.drop(C.TS_COL):
        var = next(v for v in VARS if v in col)
        lo, hi = RANGES[var]
        bad = df[col].dropna().pipe(lambda s: s[(s < lo) | (s > hi)])
        assert bad.empty, f"{name}: {col} has {len(bad)} values outside {lo}..{hi}"
    return {c: round(float(df[c].notna().mean()), 4) for c in df.columns.drop(C.TS_COL)}


def sanity(obs: pd.DataFrame, fc: pd.DataFrame, grid: pd.DataFrame) -> dict:
    """Correlations on TRAINING hours only (before SPLIT_DATE), so nothing here peeks at test.
    1) per variable: day-ahead forecast vs what was observed, per point and averaged;
    2) do our wind points track PJM's wind share? (forecast and observed wind)."""
    df = obs.merge(fc, on=C.TS_COL).merge(grid[[C.TS_COL, "wind_share"]], on=C.TS_COL, how="left")
    df = df[df[C.TS_COL] < pd.Timestamp(C.SPLIT_DATE, tz="UTC")]
    out: dict = {"hours_used": f"{df[C.TS_COL].min()} -> {df[C.TS_COL].max()}",
                 "note": "Pearson r; train hours only (< SPLIT_DATE)", "forecast_vs_observed": {}}
    for v in VARS:
        per_point = {p: round(float(df[f"{p}_{v}"].corr(df[f"{p}_{v}_fc{FC_DAY}"])), 3)
                     for p in POINTS}
        mean_r = round(sum(per_point.values()) / len(per_point), 3)
        out["forecast_vs_observed"][v] = {"mean_over_points": mean_r, "per_point": per_point}

    fc_wind = df[[f"{p}_wind_speed_100m_fc{FC_DAY}" for p in WIND_POINTS]].mean(axis=1)
    obs_wind = df[[f"{p}_wind_speed_100m" for p in WIND_POINTS]].mean(axis=1)
    share = df["wind_share"]
    out["wind_vs_pjm_wind_share"] = {
        "fc_mean_wind_points_pearson": round(float(fc_wind.corr(share)), 3),
        "fc_mean_wind_points_spearman": round(float(fc_wind.corr(share, method="spearman")), 3),
        "obs_mean_wind_points_pearson": round(float(obs_wind.corr(share)), 3),
        "obs_chicago_only_pearson": round(float(df["chicago_wind_speed_100m"].corr(share)), 3),
    }
    return out


def main() -> None:
    end = date.today() - timedelta(days=1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obs = fetch_points("obs", START, end)
    fc = fetch_points("fc", START, end)
    cov_obs, cov_fc = validate(obs, "obs"), validate(fc, "fc")
    obs.to_csv(OBS_CSV, index=False)
    fc.to_csv(FC_CSV, index=False)

    grid = pd.read_csv(C.RAW_DIR / f"gridgreen_{C.EIA_BALANCING_AUTHORITY}.csv")
    grid[C.TS_COL] = pd.to_datetime(grid[C.TS_COL], utc=True)
    report = sanity(obs, fc, grid)
    report["coverage_obs"], report["coverage_fc"] = cov_obs, cov_fc
    SANITY_JSON.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {OBS_CSV} and {FC_CSV}: {len(obs)} hourly rows, "
          f"{obs[C.TS_COL].min():%Y-%m-%d} -> {obs[C.TS_COL].max():%Y-%m-%d %H:%M}")
    print(f"coverage obs {min(cov_obs.values()):.1%}..{max(cov_obs.values()):.1%}, "
          f"fc {min(cov_fc.values()):.1%}..{max(cov_fc.values()):.1%}")
    print(json.dumps({k: report[k] for k in ("forecast_vs_observed", "wind_vs_pjm_wind_share")},
                     indent=1))


if __name__ == "__main__":
    main()
