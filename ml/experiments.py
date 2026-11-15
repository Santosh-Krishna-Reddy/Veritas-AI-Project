"""Select the pre-registered feature ladder on validation, then score test once."""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from ml import config as C
from ml.evaluate import cleanest_k_overlap
from ml.features import (TARGET_COL, TARGET_TS_COL, build_ladder_features,
                         feature_columns, lag_only_columns, restrict_to_period)

GROUPS = tuple(f"G{i}" for i in range(7))
SELECTION_RULE = (
    "final = the step with the lowest validation MAE; within 0.2 g/kWh, "
    "prefer fewer features"
)


def missing_groups() -> dict[str, str]:
    """Return unavailable groups and the pre-registered reason for skipping them."""
    extra = C.RAW_DIR / "extra"
    required = {
        "G3": extra / "grid_extra_PJM.csv",
        "G4": extra / "weather_obs_points.csv",
        "G5": extra / "weather_fc1_points.csv",
        "G6": extra / "grid_extra_PJM.csv",
    }
    missing = {
        group: "skipped: file missing"
        for group, path in required.items()
        if not path.exists()
    }
    if "G6" not in missing:
        columns = pd.read_csv(required["G6"], nrows=0).columns
        if not any("demand" in col.lower() and "forecast" in col.lower() for col in columns):
            missing["G6"] = "skipped: file missing"
    return missing


def group_columns(feat: pd.DataFrame, group: str) -> list[str]:
    """Return the pre-registered model inputs for one available ladder step."""
    return lag_only_columns(feat) if group == "G0" else feature_columns(feat)


def fit_model(feat: pd.DataFrame, group: str) -> HistGradientBoostingRegressor:
    """Fit one deterministic ladder model and return it."""
    cols = group_columns(feat, group)
    model = HistGradientBoostingRegressor(**C.MODEL_PARAMS)
    model.fit(feat[cols], feat[TARGET_COL])
    return model


def score(feat: pd.DataFrame, predictions: np.ndarray) -> dict[str, float]:
    """Calculate the two reportable metrics for a prediction array."""
    pred = pd.Series(predictions, index=feat.index)
    return {
        "mae": float(np.mean(np.abs(feat[TARGET_COL].to_numpy() - predictions))),
        f"cleanest_{C.CLEANEST_K}_overlap": cleanest_k_overlap(feat, pred),
    }


def validation_results(train: pd.DataFrame, groups: list[str]) -> dict[str, dict]:
    """Fit before May and score May-July without touching test data."""
    results = {}
    for group in groups:
        feat = build_ladder_features(train, group)
        fit = restrict_to_period(feat, end=C.VALIDATION_START)
        val = restrict_to_period(feat, start=C.VALIDATION_START, end=C.SPLIT_DATE)
        model = fit_model(fit, group)
        results[group] = {
            "features": len(group_columns(feat, group)),
            "validation": score(val, model.predict(val[group_columns(val, group)])),
        }
    return results


def select_group(results: dict[str, dict]) -> str:
    """Apply the written 0.2 g/kWh simplicity tie-break without test scores."""
    best = min(item["validation"]["mae"] for item in results.values())
    eligible = [
        group
        for group in results
        if results[group]["validation"]["mae"] <= best + 0.2
    ]
    return min(eligible, key=lambda group: int(group[1:]))


def test_results(
    train: pd.DataFrame, test: pd.DataFrame, groups: list[str]
) -> tuple[dict, dict, pd.DataFrame]:
    """Refit available steps on training data and score the held-out test once."""
    full = pd.concat([train, test], ignore_index=True)
    results, models, prediction_frame = {}, {}, None
    for group in groups:
        train_feat = restrict_to_period(
            build_ladder_features(train, group), end=C.SPLIT_DATE
        )
        test_feat = restrict_to_period(
            build_ladder_features(full, group), start=C.SPLIT_DATE
        )
        model = fit_model(train_feat, group)
        predictions = model.predict(test_feat[group_columns(test_feat, group)])
        results[group] = score(test_feat, predictions)
        models[group] = model
        if prediction_frame is None:
            prediction_frame = test_feat[[C.TS_COL, TARGET_TS_COL, TARGET_COL]].copy()
        prediction_frame[f"pred_{group.lower()}"] = predictions
    return results, models, prediction_frame


def write_outputs(results: dict, selected: str, models: dict, predictions: pd.DataFrame) -> None:
    """Write ablation, metrics, artifacts, and per-row predictions."""
    C.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (C.RESULTS_DIR / "ablation.json").write_text(json.dumps(results, indent=2))
    metrics_path = C.RESULTS_DIR / "metrics.json"
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
    for group in GROUPS[2:]:
        item = results[group]
        metrics[f"model_{group.lower()}"] = item.get("test", {"status": item["status"]})
    metrics["model_v2"] = {**results[selected]["test"], "selected_group": selected}
    metrics_path.write_text(json.dumps(metrics, indent=2))
    old_predictions = pd.read_csv(C.RESULTS_DIR / "test_predictions.csv")
    old_targets = pd.to_datetime(old_predictions[TARGET_TS_COL], utc=True)
    new_targets = pd.to_datetime(predictions[TARGET_TS_COL], utc=True)
    if len(old_predictions) != len(predictions) or not old_targets.equals(new_targets):
        raise ValueError("test prediction rows do not match the locked test period")
    for col in [name for name in predictions if name.startswith("pred_")]:
        old_predictions[col] = predictions[col].to_numpy()
    old_predictions["pred_model_v2"] = predictions[f"pred_{selected.lower()}"].to_numpy()
    old_predictions.to_csv(C.RESULTS_DIR / "test_predictions.csv", index=False)
    joblib.dump(models[selected], C.ARTIFACTS_DIR / "model_v2.joblib")


def main() -> None:
    """Run validation selection before the single held-out test scoring pass."""
    train = pd.read_csv(C.PROCESSED_DIR / "train.csv", parse_dates=[C.TS_COL])
    test = pd.read_csv(C.PROCESSED_DIR / "test.csv", parse_dates=[C.TS_COL])
    missing = missing_groups()
    groups = [group for group in GROUPS if group not in missing]
    if groups != ["G0", "G1", "G2"]:
        raise RuntimeError("extra files appeared, but G3-G6 joins are not implemented")
    results = validation_results(train, groups)
    selected = select_group(results)
    validation = {group: item["validation"] for group, item in results.items()}
    print(json.dumps(validation, indent=2))
    print(f"selected on validation: {selected}")
    test_scores, models, predictions = test_results(train, test, groups)
    for group in groups:
        results[group].update(status="completed", test=test_scores[group])
    for group, status in missing.items():
        results[group] = {"status": status}
    output = {
        "_meta": {"selection_rule": SELECTION_RULE, "selected_group": selected},
        **{group: results[group] for group in GROUPS},
    }
    write_outputs(output, selected, models, predictions)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
