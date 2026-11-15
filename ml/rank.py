"""Why does the model beat persistence on MAE but not on cleanest-3-hours overlap?

Overlap only looks at the ORDER of hours inside a day (see evaluate.cleanest_k_overlap),
so we measure how well each forecast gets the within-day SHAPE right, then try
shape-aware variants. Writes results/ranking_diagnosis.json and adds new keys to
results/metrics.json (never touching the keys evaluate.py owns).

Run after `make eval`:  .venv/bin/python -m ml.rank
"""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from ml import config as C
from ml.baseline import BASELINES, persistence
from ml.evaluate import cleanest_k_overlap, evaluate, test_features
from ml.features import (TARGET_COL, TARGET_TS_COL, build_features, feature_columns,
                         model_inputs, restrict_to_period)
from ml.train import LAGS_ONLY_PATH, MODEL_PATH

OVERLAP = f"cleanest_{C.CLEANEST_K}_overlap"
LAG_COLS = [f"ci_lag_{i}" for i in range(C.LAG_HOURS)]
# Validation = the last 3 months of TRAIN. Variants are also scored here, so a test "win"
# can be checked against data we never used for the final test.
VAL_START = "2026-05-01"
BOOTSTRAP_ROUNDS = 2000


def full_days(feat: pd.DataFrame) -> pd.Series:
    """Boolean mask: rows whose target day (UTC) has all 24 hours. Same rule as overlap."""
    day = feat[TARGET_TS_COL].dt.date
    return day.map(day.value_counts()) == 24


def within_day_deviation(feat: pd.DataFrame, values: np.ndarray) -> np.ndarray:
    """Each value minus the mean of its target day: the 'shape' with the level removed."""
    s = pd.Series(np.asarray(values), index=feat.index)
    return (s - s.groupby(feat[TARGET_TS_COL].dt.date).transform("mean")).values


def deviation_corr(feat: pd.DataFrame, pred: pd.Series) -> float:
    """Pearson correlation of predicted vs true within-day deviation, full days only."""
    m = full_days(feat).values
    f = feat[m]
    true_dev = within_day_deviation(f, f[TARGET_COL].values)
    pred_dev = within_day_deviation(f, pred.values[m])
    return float(np.corrcoef(true_dev, pred_dev)[0, 1])


def per_day_overlap(feat: pd.DataFrame, pred: pd.Series) -> pd.Series:
    """Overlap score for every full test day (same metric, one number per day)."""
    pred = pd.Series(pred.values, index=feat.index)
    m = full_days(feat)
    return pd.Series({d: cleanest_k_overlap(g, pred[g.index])
                      for d, g in feat[m].groupby(feat[TARGET_TS_COL].dt.date)})


def paired_vs_persistence(feat: pd.DataFrame, pred: pd.Series, base: pd.Series) -> dict:
    """Day-by-day comparison with persistence, plus a bootstrap 95% interval on the gap.
    Bootstrap = resample test days with replacement many times; if the interval contains 0,
    the difference could be luck of which days landed in the test period."""
    diff = per_day_overlap(feat, pred) - per_day_overlap(feat, base)
    rng = np.random.default_rng(C.SEED)
    boots = [rng.choice(diff.values, len(diff)).mean() for _ in range(BOOTSTRAP_ROUNDS)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"days": int(len(diff)), "days_better": int((diff > 0).sum()),
            "days_worse": int((diff < 0).sum()), "days_tied": int((diff == 0).sum()),
            "mean_overlap_gap": float(diff.mean()), "bootstrap_95ci": [float(lo), float(hi)]}


def fit(feat: pd.DataFrame, cols: list[str], target: str) -> HistGradientBoostingRegressor:
    """Same model and settings as ml/train.py, just a different target column."""
    return HistGradientBoostingRegressor(**C.MODEL_PARAMS).fit(feat[cols], feat[target])


def add_day_targets(feat: pd.DataFrame) -> pd.DataFrame:
    """Training-only targets per full target day: day_mean, dev (= target - day_mean) and
    rank_pct (the hour's rank in its day, 1/24 = cleanest .. 1 = dirtiest). These use the
    whole target day, which is fine for a TARGET; they are never used as inputs."""
    f = feat[full_days(feat)].copy()
    by_day = f.groupby(f[TARGET_TS_COL].dt.date)[TARGET_COL]
    f["day_mean"] = by_day.transform("mean")
    f["dev"] = f[TARGET_COL] - f["day_mean"]
    f["rank_pct"] = by_day.rank(pct=True, method="first")
    return f


def variant_preds(train_feat: pd.DataFrame, eval_feat: pd.DataFrame) -> dict[str, pd.Series]:
    """Fit every shape-aware variant on train_feat and predict eval_feat."""
    cols = feature_columns(train_feat)
    t = add_day_targets(train_feat)
    X = eval_feat[cols]
    out = {"model_plain_refit": fit(t, cols, TARGET_COL).predict(X)}
    # (a) Learn the shape (deviation from the day's mean) separately from the level, then add
    # a level back: either a learned daily mean, or simply today's mean (last 24 h), which
    # barely changes from hour to hour and so cannot scramble the predicted shape.
    dev = fit(t, cols, "dev").predict(X)
    out["model_deviation"] = dev + fit(t, cols, "day_mean").predict(X)
    out["model_deviation_today_mean"] = dev + eval_feat[LAG_COLS].mean(axis=1).values
    return {k: pd.Series(v, index=eval_feat.index) for k, v in out.items()}


def validation_scores(all_feat: pd.DataFrame) -> dict:
    """Refit on targets before VAL_START, score persistence and every variant on
    [VAL_START, SPLIT_DATE). Test data is not touched here."""
    tr = restrict_to_period(all_feat, end=VAL_START)
    va = restrict_to_period(all_feat, start=VAL_START, end=C.SPLIT_DATE)
    preds = {"persistence": persistence(va), **variant_preds(tr, va)}
    return {"period": f"{VAL_START} to {C.SPLIT_DATE} (last 3 months of train)",
            "scores": evaluate(va, preds)}


def main() -> None:
    train_df = pd.read_csv(C.PROCESSED_DIR / "train.csv", parse_dates=[C.TS_COL])
    train_feat = restrict_to_period(build_features(train_df), end=C.SPLIT_DATE)
    feat = test_features()

    # Existing forecasts, scored exactly like evaluate.py does.
    preds = {name: fn(feat) for name, fn in BASELINES.items()}
    for name, path in [("model", MODEL_PATH), ("model_lags_only", LAGS_ONLY_PATH)]:
        m = joblib.load(path)
        preds[name] = pd.Series(m.predict(model_inputs(m, feat)), index=feat.index)
    new = variant_preds(train_feat, feat)
    new.pop("model_plain_refit")  # only needed on validation; test uses the saved model
    preds.update(new)

    scores = evaluate(feat, preds)
    base = scores["persistence"][OVERLAP]
    diagnosis = {
        "how_overlap_is_computed": (
            "For each UTC target day with all 24 hours: take the 3 hours with the lowest "
            "true CI and the 3 with the lowest predicted CI; score = shared hours / 3. "
            "Average over days. Only the order within a day matters; the level does not. "
            "Random picking scores 0.125."),
        "test_period": f"{feat[TARGET_TS_COL].min():%Y-%m-%d} to {feat[TARGET_TS_COL].max():%Y-%m-%d}",
        "within_day_deviation_corr": {k: deviation_corr(feat, p) for k, p in preds.items()},
        "vs_persistence_day_by_day": {k: paired_vs_persistence(feat, p, preds["persistence"])
                                      for k, p in preds.items() if k != "persistence"},
        "test_scores": {k: {**v, "beats_persistence_on_overlap": v[OVERLAP] > base}
                        for k, v in scores.items()},
        "validation": validation_scores(train_feat),
    }
    winners = [k for k in new if scores[k][OVERLAP] > base]
    diagnosis["headline"] = (
        f"HEADLINE IMPROVEMENT: {', '.join(winners)} beat persistence on overlap"
        if winners else "NO VARIANT BEATS PERSISTENCE ON OVERLAP (honest negative result)")

    out = C.RESULTS_DIR / "ranking_diagnosis.json"
    out.write_text(json.dumps(diagnosis, indent=2))
    metrics_path = C.RESULTS_DIR / "metrics.json"
    metrics = json.loads(metrics_path.read_text())
    metrics.update({k: scores[k] for k in new})  # only our own new keys
    metrics_path.write_text(json.dumps(metrics, indent=2))
    print(json.dumps(diagnosis, indent=2))


if __name__ == "__main__":
    main()
