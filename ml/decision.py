"""Post-hoc hour-selection audit of committed held-out predictions.

Run: python -m ml.decision
This metric was chosen after inspecting the original test set: descriptive only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "test_predictions.csv"
OUTPUT = ROOT / "results" / "decision_metrics.json"
MODEL_COLUMNS = ("pred_model", "pred_persistence")


def full_days(df: pd.DataFrame, timezone: str = "UTC") -> list[pd.DataFrame]:
    """Only days with all expected hours; account for Chicago DST days."""
    local = df["target_timestamp"].dt.tz_convert(timezone)
    groups = []
    for day, group in df.groupby(local.dt.date, sort=True):
        first = pd.Timestamp(day).tz_localize(timezone)
        expected = int((first + pd.DateOffset(days=1) - first) / pd.Timedelta(hours=1))
        if len(group) != expected or group["target_timestamp"].duplicated().any():
            continue
        groups.append(group.sort_values("target_timestamp"))
    return groups


def one_day(group: pd.DataFrame, column: str, k: int) -> dict:
    """Evaluate actual carbon intensity at the selected hours (not predictions)."""
    truth = group["target"].to_numpy(dtype=float)
    pred = group[column].to_numpy(dtype=float)
    true_ix = np.argsort(truth, kind="stable")[:k]
    pred_ix = np.argsort(pred, kind="stable")[:k]
    oracle = float(truth[true_ix].mean())
    picked = float(truth[pred_ix].mean())
    average = float(truth.mean())
    possible = average - oracle
    return {
        "regret_g_per_kwh": picked - oracle,
        "saved_g_per_kwh": average - picked,
        "captured_fraction": (average - picked) / possible if possible > 1e-12 else None,
        "cleanest_k_overlap": len(set(true_ix) & set(pred_ix)) / k,
        "picked_ci_g_per_kwh": picked,
        "oracle_ci_g_per_kwh": oracle,
        "day_average_ci_g_per_kwh": average,
    }


def average_days(days: list[dict]) -> dict:
    """Macro-average each day, including fractional capture over valid days."""
    keys = days[0].keys()
    return {key: float(np.mean([d[key] for d in days if d[key] is not None]))
            for key in keys}


def bootstrap_gap(groups: list[pd.DataFrame], reps: int = 6000) -> dict:
    """Day-resampling CI for model regret minus persistence regret, fixed LCG seed."""
    differences = [
        one_day(g, "pred_model", 3)["regret_g_per_kwh"]
        - one_day(g, "pred_persistence", 3)["regret_g_per_kwh"]
        for g in groups
    ]
    state = 42
    scores = []
    for _ in range(reps):
        sampled = 0.0
        for _ in differences:
            state = (1664525 * state + 1013904223) % (2 ** 32)
            sampled += differences[int((state / 2 ** 32) * len(differences))]
        scores.append(sampled / len(differences))
    lo, hi = np.quantile(scores, [0.025, 0.975])
    return {"seed": 42, "replicates": reps, "model_minus_persistence_g_per_kwh":
            float(np.mean(differences)), "ci_95": [float(lo), float(hi)]}


def calculate(df: pd.DataFrame) -> dict:
    """Compute UTC main metric, Chicago sensitivity and predeclared k sensitivities."""
    df = df.copy()
    df["target_timestamp"] = pd.to_datetime(df["target_timestamp"], utc=True)
    df = df.sort_values("target_timestamp")
    utc = full_days(df, "UTC")
    if not utc:
        raise ValueError("No complete UTC days")
    names = [x.removeprefix("pred_") for x in df if x.startswith("pred_")
             and not x.endswith(("_lo", "_hi"))]
    models = {}
    for name in names:
        col = "pred_" + name
        record = average_days([one_day(g, col, 3) for g in utc])
        record["mae_g_per_kwh"] = float((df["target"] - df[col]).abs().mean())
        models[name] = record
    gap = [np.sort(g["target"].to_numpy())[5] - np.sort(g["target"].to_numpy())[2]
           for g in utc]
    variants = {}
    for zone in ("UTC", "America/Chicago"):
        selected = full_days(df, zone)
        for k in (1, 3, 6):
            variants[f"{zone}|k={k}"] = {
                "days": len(selected),
                "model": (average_days([one_day(g, "pred_model", k) for g in selected])
                          if selected else None),
                "persistence": (average_days(
                    [one_day(g, "pred_persistence", k) for g in selected])
                                if selected else None),
            }
    return {
        "_note": "Added Nov 15 after the first test results were seen. "
                 "Report next to cleanest-3 overlap, not instead of it.",
        "_scope": "Retrospective held-out analysis; not a prospective real-time forecast test.",
        "source": "results/test_predictions.csv",
        "rows": len(df),
        "full_utc_days": len(utc),
        "models": models,
        "model_minus_persistence_regret_bootstrap": bootstrap_gap(utc),
        "flat_bottom_gap_third_to_sixth_g_per_kwh": {
            "p10": float(np.quantile(gap, 0.1)),
            "median": float(np.quantile(gap, 0.5)),
            "p90": float(np.quantile(gap, 0.9)),
        },
        "sensitivity": variants,
    }


def main() -> None:
    result = calculate(pd.read_csv(INPUT))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"models": result["models"],
                      "bootstrap": result["model_minus_persistence_regret_bootstrap"]},
                     indent=2))


if __name__ == "__main__":
    main()
