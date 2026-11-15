"""Read-only data for the web page. Every number the page shows is computed or read here.

Sources: the trained model (ml/artifacts/), data/processed/ (written by `make data`) and the
files under results/ (written by `make eval`, `make rank`, `make failures`). Nothing here
trains, tunes or re-splits anything.
"""

from __future__ import annotations

import json
import re

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException

from ml import config as C
from ml.baseline import persistence
from ml.failures import daily_errors
from ml.features import TARGET_COL, TARGET_TS_COL, build_features, model_inputs
from ml.recommend import recommend
from ml.train import MODEL_PATH

DISPLAY_TZ = "America/Chicago"  # Chicago (ComEd) is our reference point, as in app.py
HISTORY_HOURS = 192  # 168 for the last-week lag + 24 for the lag window (same as app.py)
MODEL_KEY = "model"  # the metrics.json key of the model whose forecast we serve


def _local(ts: pd.Timestamp) -> str:
    return ts.tz_convert(DISPLAY_TZ).isoformat()


def load_processed() -> pd.DataFrame:
    """All processed hours (train + test), sorted, UTC. 503 if `make data` has not run."""
    paths = [C.PROCESSED_DIR / f"{s}.csv" for s in ("train", "test")]
    if not all(p.exists() for p in paths):
        raise HTTPException(503, "no processed data yet: run `make data`")
    df = pd.concat([pd.read_csv(p, parse_dates=[C.TS_COL]) for p in paths], ignore_index=True)
    if df[C.TS_COL].dt.tz is None:
        df[C.TS_COL] = df[C.TS_COL].dt.tz_localize("UTC")
    return df.sort_values(C.TS_COL).reset_index(drop=True)


def _model():
    if not MODEL_PATH.exists():
        raise HTTPException(503, "model not trained yet: run `make train`")
    return joblib.load(MODEL_PATH)


def _predict_next_24h(hist: pd.DataFrame) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray]:
    """Model + persistence forecast for the 24 hours after the last observed hour.

    Same logic as app.py `_forecast_next_24h` (copied, because importing app.py loads
    Gradio, which takes ~30 s). Placeholder hours are forward-filled only so
    build_features can form the lag window; each row reads lags at or before its own time.
    """
    model = _model()
    last_ts = hist[C.TS_COL].iloc[-1]
    pad_ts = pd.date_range(last_ts + pd.Timedelta(hours=1), periods=24, freq="h", tz="UTC")
    combined = pd.concat([hist, pd.DataFrame({C.TS_COL: pad_ts, C.CI_COL: np.nan})],
                         ignore_index=True)
    combined[C.CI_COL] = combined[C.CI_COL].ffill()
    feat = build_features(combined).tail(24)
    preds = np.asarray(model.predict(model_inputs(model, feat)), dtype=float)
    return pad_ts, preds, persistence(feat).to_numpy(dtype=float)


def forecast(load_kwh: float) -> dict:
    """Next-24-hour forecast, cleanest hours and CO2 saved for a load in kWh."""
    hist = load_processed().tail(HISTORY_HOURS).reset_index(drop=True)
    # The one place to switch to ml/predict.py latest_forecast() once MODEL ships it;
    # lo/hi (10-90 % band) stay None until then.
    ts, preds, persist = _predict_next_24h(hist)
    lo = hi = [None] * 24
    rec = recommend(list(preds), load_kwh)
    hours = [{"ts_utc": t.isoformat(), "ts_local": _local(t), "forecast": round(float(p), 1),
              "lo": lo[i], "hi": hi[i], "persistence": round(float(persist[i]), 1)}
             for i, (t, p) in enumerate(zip(ts, preds))]
    return {
        "issued_for_date": ts[0].tz_convert(DISPLAY_TZ).date().isoformat(),
        "data_through_utc": hist[C.TS_COL].iloc[-1].isoformat(),
        "region": C.REGION_NAME,
        "timezone": DISPLAY_TZ,
        "model_key": MODEL_KEY,
        "load_kwh": load_kwh,
        "hours": hours,
        "cleanest_hours": [hours[i]["ts_local"] for i in rec["cleanest_hours_utc"]],
        "dirtiest_hour": hours[rec["dirtiest_hour_utc"]]["ts_local"],
        "co2_saved_kg": rec["co2_saved_kg"],
    }


def _read_json(name: str) -> dict | None:
    path = C.RESULTS_DIR / name
    return json.loads(path.read_text()) if path.exists() else None


def verdict(metrics: dict, ranking: dict | None) -> str:
    """Plain-English model-vs-persistence sentence, built only from the numbers passed in."""
    m, p = metrics[MODEL_KEY], metrics["persistence"]
    mae = (f"The model's forecasts are closer than \"tomorrow = today\" (MAE {m['mae']:.2f} "
           f"vs {p['mae']:.2f} gCO2/kWh)" if m["mae"] < p["mae"] else
           f"The model's forecasts are NOT closer than \"tomorrow = today\" (MAE "
           f"{m['mae']:.2f} vs {p['mae']:.2f} gCO2/kWh)")
    ci = (ranking or {}).get("vs_persistence_day_by_day", {}).get(MODEL_KEY, {}).get(
        "bootstrap_95ci")
    mo, po = m["cleanest_3_overlap"], p["cleanest_3_overlap"]
    if ci and ci[0] <= 0 <= ci[1]:
        pick = (f"but it ties persistence on picking the 3 cleanest hours ({mo:.3f} vs "
                f"{po:.3f}; 95% interval of the gap {ci[0]:+.3f} to {ci[1]:+.3f} includes 0)")
    else:
        word = "beats" if mo > po else "loses to"
        pick = f"and it {word} persistence on picking the 3 cleanest hours ({mo:.3f} vs {po:.3f})"
    return f"{mae}, {pick}."


def metrics() -> dict:
    """results/metrics.json merged with the optional decision/ablation/ranking files."""
    base = _read_json("metrics.json")
    if base is None:
        raise HTTPException(503, "no results/metrics.json yet: run `make eval`")
    out = {"metrics": base}
    for key, name in (("decision", "decision_metrics.json"), ("ablation", "ablation.json"),
                      ("ranking", "ranking_diagnosis.json")):
        out[key] = _read_json(name)
    out["verdict"] = verdict(base, out["ranking"])
    return out


def _explanations() -> tuple[dict[str, str], str]:
    """Per-day 'why' paragraphs and the closing pattern paragraph from results/failures.md."""
    path = C.RESULTS_DIR / "failures.md"
    text = path.read_text() if path.exists() else ""
    days = dict(re.findall(r"^\*\*(\d{4}-\d{2}-\d{2}) \(\w+\)\.\*\* (.+)$", text, re.M))
    pat = re.search(r"^\*\*Pattern\.\*\* (.+)$", text, re.M)
    return days, pat.group(1) if pat else ""


def failures() -> dict:
    """The worst test days (from failure_features.csv), each with MAE, drivers and hourly data."""
    feat_path = C.RESULTS_DIR / "failure_features.csv"
    pred_path = C.RESULTS_DIR / "test_predictions.csv"
    if not (feat_path.exists() and pred_path.exists()):
        raise HTTPException(503, "no failure analysis yet: run `make eval && make failures`")
    feats = pd.read_csv(feat_path)
    pred = pd.read_csv(pred_path, parse_dates=[TARGET_TS_COL])
    err = daily_errors(pred)
    err.index = err.index.map(str)
    why, pattern = _explanations()
    days = []
    for day in feats["day"].unique():
        hourly = pred[pred[TARGET_TS_COL].dt.date.map(str) == day]
        days.append({
            "day": day,
            **{k: round(float(err.at[day, k]), 1) for k in
               ("model_mae", "persistence_mae", "true_mean", "bias")},
            "error_type": err.at[day, "error_type"],
            "explanation": why.get(day, ""),
            "features": feats[feats["day"] == day].drop(columns="day").to_dict("records"),
            "hours": [{"ts_utc": t.isoformat(), "true": round(y, 1), "model": round(m, 1),
                       "persistence": round(p, 1)} for t, y, m, p in zip(
                hourly[TARGET_TS_COL], hourly[TARGET_COL], hourly["pred_model"],
                hourly["pred_persistence"])],
        })
    days.sort(key=lambda d: d["model_mae"], reverse=True)
    return {"days": days, "pattern": pattern}


def history(days: int) -> dict:
    """The last `days` x 24 observed hours of carbon intensity."""
    df = load_processed().tail(days * 24)
    return {"region": C.REGION_NAME, "hours": [
        {"ts_utc": t.isoformat(), "ts_local": _local(t), "carbon_intensity": round(float(v), 1)}
        for t, v in zip(df[C.TS_COL], df[C.CI_COL])]}
