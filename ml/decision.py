"""Decision quality: how much CO2 would a user really emit by following each forecast?

Cleanest-3 overlap only counts exact hour matches. Here we score what matters to the user:
the TRUE carbon intensity of the hours a forecast tells them to use.

Per full target day and per forecast (every pred_* column in results/test_predictions.csv):
  picked_ci = mean TRUE intensity of the k hours the forecast picks
  oracle_ci = mean of the k truly cleanest hours (best possible pick)
  day_avg   = mean of all hours that day (what "no planning" costs on average)
  worst_ci  = mean of the k truly dirtiest hours
  regret    = picked_ci - oracle_ci        (g/kWh, lower is better, 0 = perfect)
  saved     = day_avg - picked_ci          (g/kWh saved vs running at an average hour)
  captured  = saved / (day_avg - oracle_ci) (share of the possible saving, 1 = perfect)

Reads: results/test_predictions.csv, data/raw/gridgreen_PJM.csv (wind share, all-data shape)
Writes: results/decision_metrics.json
Run: python -m ml.decision
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ml import config as C

PRED_PATH = C.RESULTS_DIR / "test_predictions.csv"
OUT_PATH = C.RESULTS_DIR / "decision_metrics.json"
RAW_PATH = C.RAW_DIR / f"gridgreen_{C.EIA_BALANCING_AUTHORITY}.csv"
LOCAL_TZ = "America/Chicago"
KS = [1, 3, 6]               # sensitivity: how many hours the user runs the load for
N_BOOT = 2000                # bootstrap resamples (by day)
PRIMARY = ("UTC", C.CLEANEST_K)  # same day grouping and k as ml/evaluate.py
NOTE = ("Added Nov 15 after the first test results were seen. "
        "Reported next to cleanest-3 overlap, not instead of it.")


def load_predictions() -> pd.DataFrame:
    """Read test_predictions.csv; fail fast if the expected columns are missing."""
    df = pd.read_csv(PRED_PATH)
    need = {"target_timestamp", "target"}
    assert need <= set(df.columns), f"{PRED_PATH} lacks {need - set(df.columns)}"
    assert pred_columns(df), f"{PRED_PATH} has no pred_* columns"
    df["target_timestamp"] = pd.to_datetime(df["target_timestamp"], utc=True)
    assert df[["target"] + pred_columns(df)].notna().all().all(), "NaN in predictions"
    return df


def pred_columns(df: pd.DataFrame) -> list[str]:
    """Every forecast column (pred_*), so new forecasts are picked up automatically."""
    return [c for c in df.columns if c.startswith("pred_")]


def full_days(df: pd.DataFrame, tz: str) -> pd.DataFrame:
    """Add a 'day' column (calendar date of the target hour in `tz`) and keep only days
    that have every hour. A Chicago day has 23 or 25 hours on DST change days, so the
    expected count comes from the calendar, not a fixed 24."""
    local = df["target_timestamp"].dt.tz_convert(tz)
    out = df.assign(day=local.dt.date)
    starts = pd.to_datetime(pd.Series(out["day"].unique())).dt.tz_localize(tz)
    expected = {s.date(): int((s + pd.DateOffset(days=1) - s) / pd.Timedelta(hours=1))
                for s in starts}
    counts = out.groupby("day")["target"].transform("size")
    return out[counts == out["day"].map(expected)].reset_index(drop=True)


def day_scores(days: pd.DataFrame, k: int) -> pd.DataFrame:
    """One row per (day, forecast) with picked/oracle/day_avg/worst/regret/saved/captured
    and the exact-hour overlap. Ties are broken by nsmallest (first row wins)."""
    rows = []
    for day, g in days.groupby("day"):
        true_k = g.nsmallest(k, "target")
        base = {"day": day, "oracle_ci": true_k["target"].mean(), "day_avg": g["target"].mean(),
                "worst_ci": g.nlargest(k, "target")["target"].mean()}
        for col in pred_columns(days):
            pick = g.nsmallest(k, col)
            overlap = len(set(pick.index) & set(true_k.index)) / k
            rows.append({**base, "forecast": col.removeprefix("pred_"),
                         "picked_ci": pick["target"].mean(), "overlap": overlap})
    s = pd.DataFrame(rows)
    s["regret"] = s["picked_ci"] - s["oracle_ci"]
    s["saved"] = s["day_avg"] - s["picked_ci"]
    s["captured"] = s["saved"] / (s["day_avg"] - s["oracle_ci"])
    return s


def summarize(scores: pd.DataFrame) -> dict:
    """Average the per-day scores for each forecast. 'captured_pooled' divides the average
    saving by the average possible saving, which is less jumpy than averaging daily ratios
    when a day's curve is almost flat."""
    out = {}
    for name, g in scores.groupby("forecast", sort=False):
        out[name] = {m: float(g[m].mean()) for m in
                     ["picked_ci", "regret", "saved", "captured", "overlap"]}
        out[name]["captured_pooled"] = float(g["saved"].mean() /
                                             (g["day_avg"] - g["oracle_ci"]).mean())
    first = scores.drop_duplicates("day")
    out["_truth"] = {"days": int(len(first)), "oracle_ci": float(first["oracle_ci"].mean()),
                     "day_avg": float(first["day_avg"].mean()),
                     "worst_ci": float(first["worst_ci"].mean())}
    return out


def bootstrap_vs_persistence(scores: pd.DataFrame, metric: str = "regret") -> dict:
    """For each forecast: mean over days of (forecast - persistence) on `metric`, with a 95%
    bootstrap interval. We resample whole DAYS with replacement (seed 42), recompute the
    mean, repeat N_BOOT times and take the 2.5th and 97.5th percentiles. If the interval
    contains 0, the difference could be luck."""
    wide = scores.pivot(index="day", columns="forecast", values=metric)
    rng = np.random.default_rng(C.SEED)
    idx = rng.integers(0, len(wide), size=(N_BOOT, len(wide)))
    out = {}
    for name in wide.columns.drop("persistence"):
        diff = (wide[name] - wide["persistence"]).to_numpy()
        boots = diff[idx].mean(axis=1)
        out[name] = {"mean_diff": float(diff.mean()),
                     "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}
    return out


def flat_bottom(days: pd.DataFrame) -> dict:
    """Test the README's guess: per day, the gap (g/kWh) between the 3rd and the 6th
    cleanest TRUE hour. A small gap means picking the 'wrong' hours costs very little."""
    gaps = days.groupby("day")["target"].apply(lambda s: s.nsmallest(6).iloc[5] - s.nsmallest(3).iloc[2])
    return {"gap_3rd_to_6th": gaps.round(3).tolist(),
            "median": float(gaps.median()), "p10": float(gaps.quantile(0.1)),
            "p90": float(gaps.quantile(0.9)), "days": int(len(gaps))}


def mae_by(days: pd.DataFrame, key: pd.Series) -> dict:
    """MAE of every forecast per group of `key` (a column-like Series aligned to `days`)."""
    err = days[pred_columns(days)].sub(days["target"], axis=0).abs()
    err.columns = [c.removeprefix("pred_") for c in err.columns]
    return {str(g): v for g, v in err.groupby(key.values).mean().to_dict("index").items()}


def breakdowns(days: pd.DataFrame, scores: pd.DataFrame) -> dict:
    """MAE, overlap and regret by weekday/weekend and by month (day groups follow the
    primary UTC dates); MAE by Chicago hour of day, split weekday/weekend. Overlap and
    regret are whole-day scores, so they have no by-hour version."""
    day_type = lambda d: pd.to_datetime(pd.Series(d)).dt.day_of_week.map(lambda w: "weekend" if w >= 5 else "weekday")
    month = lambda d: pd.to_datetime(pd.Series(d)).dt.strftime("%Y-%m")
    out = {}
    for label, fn in [("day_type", day_type), ("month", month)]:
        s = scores.assign(group=fn(scores["day"]).values)
        per = s.groupby(["group", "forecast"])[["overlap", "regret"]].mean()
        out[label] = {"mae": mae_by(days, fn(days["day"])),
                      "overlap_regret": {f"{g}|{f}": v for (g, f), v in per.to_dict("index").items()},
                      "days": s.drop_duplicates("day")["group"].value_counts().to_dict()}
    hour = days["target_timestamp"].dt.tz_convert(LOCAL_TZ).dt.hour
    hour_key = hour.astype(str) + "|" + day_type(days["day"]).values
    out["hour_chicago|day_type"] = {"mae": mae_by(days, hour_key)}
    return out


def wind_vs_bias(days: pd.DataFrame, raw: pd.DataFrame) -> dict:
    """Per UTC day: change in mean TRUE wind share vs the day before, and each forecast's
    mean bias (prediction - truth). Wind share here is a diagnostic, not a model feature."""
    wind = raw.set_index("timestamp")["wind_share"]
    d = days.assign(wind_share=days["target_timestamp"].map(wind))
    daily = d.groupby("day")[["wind_share", "target"] + pred_columns(d)].mean()
    prev = wind.groupby(wind.index.date).mean().shift(1)  # day before, may lie in train
    daily["d_wind"] = daily["wind_share"] - prev.reindex(daily.index).values
    out = {"day": [str(x) for x in daily.index], "d_wind_share": daily["d_wind"].round(5).tolist()}
    for col in pred_columns(d):
        bias = daily[col] - daily["target"]
        name = col.removeprefix("pred_")
        out[f"bias_{name}"] = bias.round(3).tolist()
        out[f"r_{name}"] = float(np.corrcoef(daily["d_wind"], bias)[0, 1])
    return out


def load_raw() -> pd.DataFrame:
    """The committed tidy PJM CSV with a UTC timestamp."""
    raw = pd.read_csv(RAW_PATH)
    assert {"timestamp", C.CI_COL, "wind_share"} <= set(raw.columns), f"{RAW_PATH} columns"
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True)
    return raw


def daily_shape(raw: pd.DataFrame) -> dict:
    """Mean intensity by Chicago hour of day x calendar month over ALL data (train + test)."""
    local = raw["timestamp"].dt.tz_convert(LOCAL_TZ)
    grid = raw.groupby([local.dt.month, local.dt.hour])[C.CI_COL].mean().unstack()
    by_hour = grid.mean(axis=0)
    return {"grid": grid.round(2).values.tolist(), "months": grid.index.tolist(),
            "hours": grid.columns.tolist(), "cleanest_hour": int(by_hour.idxmin()),
            "dirtiest_hour": int(by_hour.idxmax()),
            "cleanest_hour_per_month": [int(h) for h in grid.idxmin(axis=1)],
            "mean_daily_swing": float((grid.max(axis=1) - grid.min(axis=1)).mean()),
            "first": f"{raw['timestamp'].min():%Y-%m-%d}", "last": f"{raw['timestamp'].max():%Y-%m-%d}"}


def worst_model_day(days: pd.DataFrame) -> dict:
    """The UTC test day with the highest model MAE (for the 'one week' figure)."""
    col = "pred_model" if "pred_model" in days else pred_columns(days)[0]
    mae = days.assign(e=(days[col] - days["target"]).abs()).groupby("day")["e"].mean()
    p = days.assign(e=(days["pred_persistence"] - days["target"]).abs()).groupby("day")["e"].mean()
    day = mae.idxmax()
    return {"forecast": col.removeprefix("pred_"), "day": str(day),
            "mae": float(mae[day]), "persistence_mae": float(p[day])}


def main() -> None:
    preds, raw = load_predictions(), load_raw()
    out = {"_note": NOTE, "primary": {"days_grouped_by": PRIMARY[0], "k": PRIMARY[1]},
           "forecasts": [c.removeprefix("pred_") for c in pred_columns(preds)],
           "test_period": (f"{preds['target_timestamp'].min():%Y-%m-%d} to "
                           f"{preds['target_timestamp'].max():%Y-%m-%d}"),
           # Same rows and formula as results/metrics.json, repeated so figures read one file.
           "mae_all_test_rows": {c.removeprefix("pred_"): float((preds[c] - preds["target"]).abs().mean())
                                 for c in pred_columns(preds)},
           "sensitivity": {}}
    for tz in ["UTC", LOCAL_TZ]:
        days = full_days(preds, tz)
        for k in KS:
            scores = day_scores(days, k)
            out["sensitivity"][f"{tz}|k={k}"] = {
                **summarize(scores), "regret_minus_persistence": bootstrap_vs_persistence(scores)}
    utc_days = full_days(preds, "UTC")
    out["flat_bottom"] = flat_bottom(utc_days)
    out["breakdowns"] = breakdowns(utc_days, day_scores(utc_days, PRIMARY[1]))
    out["wind_vs_bias"] = wind_vs_bias(utc_days, raw)
    out["daily_shape_all_data"] = daily_shape(raw)
    out["worst_model_day"] = worst_model_day(utc_days)
    OUT_PATH.write_text(json.dumps(out, indent=2))
    main_block = out["sensitivity"][f"{PRIMARY[0]}|k={PRIMARY[1]}"]
    print(json.dumps({k: main_block[k] for k in main_block}, indent=2))
    print("flat bottom:", {k: v for k, v in out["flat_bottom"].items() if k != "gap_3rd_to_6th"})
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
