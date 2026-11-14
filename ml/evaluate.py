"""Score baselines and model on the TEST period only. Writes results/metrics.json.

Metrics:
  mae                : mean absolute error in gCO2/kWh (lower is better)
  cleanest_k_overlap : for each test day, how many of the predicted k cleanest hours are
                       truly among the k cleanest (0..1, higher is better). This is the
                       decision a user actually makes: "when should I run the load?"
Run: python -m ml.evaluate
"""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from ml import config as C
from ml.baseline import BASELINES
from ml.features import (TARGET_COL, TARGET_TS_COL, build_features,
                         feature_columns, restrict_to_period)
from ml.train import MODEL_PATH


def test_features() -> pd.DataFrame:
    """Features for rows whose target is in the test period. History may reach back into
    train (that is legitimate: by test time, yesterday is known)."""
    train = pd.read_csv(C.PROCESSED_DIR / "train.csv", parse_dates=[C.TS_COL])
    test = pd.read_csv(C.PROCESSED_DIR / "test.csv", parse_dates=[C.TS_COL])
    full = pd.concat([train, test], ignore_index=True)
    return restrict_to_period(build_features(full), start=C.SPLIT_DATE)


def cleanest_k_overlap(feat: pd.DataFrame, pred: pd.Series, k: int = C.CLEANEST_K) -> float:
    """Average over test days of |predicted cleanest k ∩ true cleanest k| / k."""
    df = pd.DataFrame({"day": feat[TARGET_TS_COL].dt.date, "hour": feat[TARGET_TS_COL].dt.hour,
                       "true": feat[TARGET_COL].values, "pred": pred.values})
    scores = []
    for _, g in df.groupby("day"):
        if len(g) < 24:
            continue  # partial day at the edge of the period
        true_k = set(g.nsmallest(k, "true")["hour"])
        pred_k = set(g.nsmallest(k, "pred")["hour"])
        scores.append(len(true_k & pred_k) / k)
    return float(np.mean(scores)) if scores else float("nan")


def evaluate(feat: pd.DataFrame, preds: dict[str, pd.Series]) -> dict:
    """Return {name: {mae, cleanest_k_overlap}} for every prediction series."""
    out = {}
    for name, p in preds.items():
        out[name] = {
            "mae": float(np.mean(np.abs(feat[TARGET_COL].values - p.values))),
            f"cleanest_{C.CLEANEST_K}_overlap": cleanest_k_overlap(feat, p),
        }
    return out


def main() -> None:
    feat = test_features()
    preds = {name: fn(feat) for name, fn in BASELINES.items()}
    model = joblib.load(MODEL_PATH)
    preds["model"] = pd.Series(model.predict(feat[feature_columns(feat)]), name="pred_model")

    metrics = evaluate(feat, preds)
    metrics["_meta"] = {
        "region": C.REGION_NAME,
        "test_period": f"{feat[TARGET_TS_COL].min():%Y-%m-%d} to {feat[TARGET_TS_COL].max():%Y-%m-%d}",
        "test_rows": int(len(feat)),
        "data_source": (C.PROCESSED_DIR / "SOURCE.txt").read_text().strip(),
    }
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (C.RESULTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # Save per-row predictions so failures.py and the README can use them.
    keep = feat[[C.TS_COL, TARGET_TS_COL, TARGET_COL]].copy()
    for name, p in preds.items():
        keep[f"pred_{name}"] = p.values
    keep.to_csv(C.RESULTS_DIR / "test_predictions.csv", index=False)

    print(json.dumps(metrics, indent=2))
    if metrics["_meta"]["data_source"].startswith("SYNTHETIC"):
        print("\n*** SYNTHETIC DATA — these numbers are NOT reportable. ***")


if __name__ == "__main__":
    main()
