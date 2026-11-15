"""Explain the days where the model was most wrong -> results/failures.md + failure_features.csv.

Run: python -m ml.evaluate first, then python -m ml.failures

For each of the worst test days we ask two questions, using only numbers:
  1. Was the error a LEVEL offset (the whole day too high/low) or a SHAPE error (wrong hours)?
  2. What changed that day? We compare each fuel share / weather column with the test-set
     average AND with the day before -- the model forecasts from yesterday's data, so a big
     day-over-day change is exactly what it cannot see coming.
Days are UTC calendar days of the forecast TARGET hour.
"""

from __future__ import annotations

import pandas as pd

from ml import config as C
from ml.features import TARGET_COL, TARGET_TS_COL

N_WORST = 5
N_DRIVERS = 2  # how many "biggest change" columns to name in the Why text
# Candidate CAUSES of a carbon swing. Coal/gas share are left out on purpose: they ARE the
# carbon intensity restated, so "coal went up" would explain nothing.
DRIVERS = ["wind_share", "solar_share", "nuclear_share", "demand_mw", "wind_ms",
           "solar_wm2", "cloud_pct", "temp_c"]
FEATURES = ["wind_share", "solar_share", "coal_share", "gas_share", "nuclear_share",
            "demand_mw", "wind_ms", "solar_wm2", "cloud_pct", "temp_c"]


def daily_errors(pred: pd.DataFrame) -> pd.DataFrame:
    """Per target day: model/persistence MAE, bias (mean error) and shape error (std of error)."""
    err = pred["pred_model"] - pred[TARGET_COL]
    day = pred[TARGET_TS_COL].dt.date
    out = pd.DataFrame({
        "model_mae": err.abs().groupby(day).mean(),
        "persistence_mae": (pred["pred_persistence"] - pred[TARGET_COL]).abs().groupby(day).mean(),
        "true_mean": pred[TARGET_COL].groupby(day).mean(),
        "pred_mean": pred["pred_model"].groupby(day).mean(),
        # Mean squared error = bias^2 + std^2. Whichever is bigger tells us the error type.
        "bias": err.groupby(day).mean(),
        "shape_err": err.groupby(day).std(ddof=0),
    })
    out["error_type"] = (out["bias"].abs() >= out["shape_err"]).map(
        {True: "level offset", False: "shape error"})
    return out


def feature_comparison(daily_feat: pd.DataFrame, days: list) -> pd.DataFrame:
    """Long table: for each bad day and feature, day mean vs day-before mean vs test average."""
    test_days = daily_feat[daily_feat.index >= pd.Timestamp(C.SPLIT_DATE).date()]
    avg = test_days[FEATURES].mean()
    # Typical size of a day-over-day change in the test period, to rank changes fairly.
    change_sd = test_days[FEATURES].diff().std()
    rows = []
    for day in days:
        prev = day - pd.Timedelta(days=1)
        for f in FEATURES:
            today, before = daily_feat.at[day, f], daily_feat.at[prev, f]
            rows.append({"day": day, "feature": f, "day_mean": today, "prev_day_mean": before,
                         "test_avg": avg[f], "ratio_to_avg": today / avg[f],
                         "change_z": (today - before) / change_sd[f]})
    return pd.DataFrame(rows)


def fmt(feature: str, value: float) -> str:
    """Shares as percentages, everything else rounded."""
    return f"{value:.1%}" if feature.endswith("_share") else f"{value:.0f}"


def drivers(comp: pd.DataFrame) -> str:
    """The N_DRIVERS cause-columns that changed most vs the day before, as short text."""
    comp = comp[comp["feature"].isin(DRIVERS)]
    top = comp.reindex(comp["change_z"].abs().sort_values(ascending=False).index).head(N_DRIVERS)
    return "; ".join(
        f"{r.feature} {fmt(r.feature, r.prev_day_mean)} -> {fmt(r.feature, r.day_mean)} "
        f"({r.ratio_to_avg:.2f}x test avg)" for r in top.itertuples())


def why(err: pd.Series, comp: pd.DataFrame) -> str:
    """One generated, numbers-only explanation paragraph for one bad day."""
    direction = "under" if err["bias"] < 0 else "over"
    gap = err["true_mean"] - err["prev_true_mean"]
    # closed = share of yesterday->today's jump the model's forecast covered (<0 = wrong way).
    moved = (f"the model moved only {err['closed']:.0%} of that gap" if err["closed"] >= 0
             else f"the model moved the wrong way ({err['closed']:.0%} of the gap)")
    return (f"{err['error_type'].capitalize()}: {direction}-predicted by "
            f"{abs(err['bias']):.0f} g on average (within-day spread {err['shape_err']:.0f} g). "
            f"True daily mean went {err['prev_true_mean']:.0f} -> {err['true_mean']:.0f} "
            f"({gap:+.0f}) vs the day before; {moved}. "
            f"Biggest day-over-day changes in possible causes: {drivers(comp)}.")


def pattern(worst: pd.DataFrame, comp: pd.DataFrame) -> str:
    """Closing paragraph: what the bad days have in common, counted from the data."""
    n_level = int((worst["error_type"] == "level offset").sum())
    wind = comp[comp["feature"] == "wind_share"].set_index("day")
    ci_change = worst["true_mean"] - worst["prev_true_mean"]
    wind_change = wind["day_mean"] - wind["prev_day_mean"]
    n_opposite = int(((ci_change * wind_change) < 0).sum())
    return (
        f"**Pattern.** {n_level} of {len(worst)} days are level offsets "
        f"(the whole day shifted up or down, the hourly shape roughly right). On every day "
        f"the true average moved by {ci_change.abs().min():.0f}-{ci_change.abs().max():.0f} g "
        f"from the day before. The model, which forecasts from yesterday's lags and "
        f"yesterday's weather, covered at most {worst['closed'].max():.0%} of that jump and "
        f"moved the wrong way on {int((worst['closed'] < 0).sum())}. On {n_opposite} of "
        f"{len(worst)} days "
        f"PJM's wind share moved opposite to carbon intensity (wind down -> dirtier, wind up -> "
        f"cleaner). Our features only contain wind observed today, so a wind change tomorrow "
        f"is invisible to the model. The fix is a weather FORECAST feature (wind/solar for "
        f"the target day); our single Chicago weather point also cannot see wind or clouds "
        f"elsewhere in the 13-state PJM footprint."
    )


def main() -> None:
    pred = pd.read_csv(C.RESULTS_DIR / "test_predictions.csv", parse_dates=[TARGET_TS_COL])
    hourly = pd.concat([pd.read_csv(C.PROCESSED_DIR / f"{s}.csv", parse_dates=[C.TS_COL])
                        for s in ("train", "test")])  # train only supplies "day before" for Aug 1
    missing = set(FEATURES + [C.CI_COL]) - set(hourly.columns)
    assert not missing, f"processed data lacks {missing}; run `make data` on the real CSV"
    daily_feat = hourly.groupby(hourly[C.TS_COL].dt.date)[FEATURES + [C.CI_COL]].mean()

    worst = daily_errors(pred).sort_values("model_mae", ascending=False).head(N_WORST)
    comp = feature_comparison(daily_feat, list(worst.index))
    comp.round(4).to_csv(C.RESULTS_DIR / "failure_features.csv", index=False)
    worst["prev_true_mean"] = [daily_feat.at[d - pd.Timedelta(days=1), C.CI_COL]
                               for d in worst.index]
    worst["closed"] = ((worst["pred_mean"] - worst["prev_true_mean"])
                       / (worst["true_mean"] - worst["prev_true_mean"]))
    reasons = {d: why(worst.loc[d], comp[comp["day"] == d]) for d in worst.index}

    lines = [
        f"# Where the model fails ({C.REGION_NAME})", "",
        f"The {N_WORST} test days (UTC) with the highest model MAE, in gCO2/kWh. Auto-written by "
        "`make failures` from `results/test_predictions.csv` and `data/processed/`; per-feature "
        "numbers are in `results/failure_features.csv`. 'Level offset' = the mean error "
        "(bias) is bigger than the within-day spread of the error.", "",
        "| Day | Weekday | Model MAE | Persistence MAE | Avg true gCO2/kWh | Error type | Why |",
        "|---|---|---|---|---|---|---|",
    ]
    for day, r in worst.iterrows():
        lines.append(f"| {day} | {pd.Timestamp(day):%a} | {r.model_mae:.0f} | "
                     f"{r.persistence_mae:.0f} | {r.true_mean:.0f} | {r.error_type} | "
                     f"{r.bias:+.0f} g all day; {drivers(comp[comp['day'] == day])} |")
    lines.append("")
    for day in worst.index:
        lines += [f"**{day} ({pd.Timestamp(day):%A}).** {reasons[day]}", ""]
    lines.append(pattern(worst, comp))
    report = "\n".join(lines) + "\n"
    assert "TODO" not in report
    (C.RESULTS_DIR / "failures.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
