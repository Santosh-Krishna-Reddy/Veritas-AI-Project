"""Produce the next 24 hourly forecasts from the latest complete observed day."""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from ml import config as C
from ml.data import clean, load_raw
from ml.features import build_ladder_features, model_inputs


def latest_complete_day(data: pd.DataFrame) -> pd.Timestamp:
    """Return the final UTC date containing all 24 observed carbon-intensity hours."""
    counts = data.groupby(data[C.TS_COL].dt.normalize()).size()
    complete = counts[counts == 24]
    if complete.empty:
        raise ValueError("no complete 24-hour day is available")
    return complete.index.max()


def forecast_features() -> pd.DataFrame:
    """Build the 24 G1 feature rows issued throughout the latest complete day."""
    data = clean(load_raw())
    origin_day = latest_complete_day(data)
    origin_end = origin_day + pd.Timedelta(hours=23)
    history = data[data[C.TS_COL] <= origin_end].copy()
    future_ts = pd.date_range(origin_end + pd.Timedelta(hours=1), periods=24, freq="h")
    pad = pd.DataFrame({C.TS_COL: future_ts, C.CI_COL: history[C.CI_COL].iloc[-1]})
    feat = build_ladder_features(pd.concat([history, pad], ignore_index=True), "G1")
    return feat[feat[C.TS_COL].dt.normalize() == origin_day].reset_index(drop=True)


def latest_forecast(model_key: str = "model_v2") -> list[dict]:
    """Return forecast, interval, persistence, and ISO timestamp for the next day."""
    model_paths = {
        "model_v2": C.ARTIFACTS_DIR / "model_v2.joblib",
        "model": C.ARTIFACTS_DIR / "model.joblib",
        "model_lags_only": C.ARTIFACTS_DIR / "model_lags_only.joblib",
    }
    if model_key not in model_paths:
        raise ValueError(f"unknown model key: {model_key}")
    feat = forecast_features()
    model = joblib.load(model_paths[model_key])
    point = model.predict(model_inputs(model, feat))
    lower, upper = interval_predictions(model_key, feat, point)
    rows = []
    for index, row in feat.iterrows():
        rows.append({
            "timestamp": row["target_timestamp"].isoformat(),
            "forecast": float(point[index]),
            "lo": float(lower[index]),
            "hi": float(upper[index]),
            "persistence": float(row["ci_lag_0"]),
        })
    if len(rows) != 24:
        raise ValueError(f"expected 24 forecast rows, got {len(rows)}")
    return rows


def interval_predictions(
    model_key: str, feat: pd.DataFrame, point: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return ordered quantile bounds, or the point forecast for legacy models."""
    if model_key != "model_v2":
        return point, point
    lo_model = joblib.load(C.ARTIFACTS_DIR / "model_v2_lo.joblib")
    hi_model = joblib.load(C.ARTIFACTS_DIR / "model_v2_hi.joblib")
    lo = lo_model.predict(model_inputs(lo_model, feat))
    hi = hi_model.predict(model_inputs(hi_model, feat))
    return np.minimum(lo, hi), np.maximum(lo, hi)
