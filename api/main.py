"""FastAPI serving layer. Run: make api   (http://localhost:8000/docs for a test UI)

POST /predict  body: {"history": [168 hourly gCO2/kWh values, oldest first], "load_kwh": 7.0}
               -> 24-hour forecast + cleanest hours + CO2 saved
GET  /health   -> {"status": "ok", "region": ...}

Read-only routes for the Next.js dashboard (web/):
GET  /api/forecast?load_kwh=7   -> next-24h forecast, 3 cleanest hours, modeled kg
GET  /api/metrics               -> committed test metrics + verdict sentence
GET  /api/failures              -> worst held-out test days with hourly data
GET  /api/history?days=7        -> observed history

Historical-replay routes over committed held-out predictions (docs/ui/api_contract.md):
GET  /api/replay/dates          -> complete 24-hour UTC days available for replay
GET  /api/replay?date=...       -> one day of forecast/persistence/observed values
GET  /api/replay/metrics        -> results/metrics.json + results/decision_metrics.json
GET  /api/replay/failures       -> grounded records parsed from results/failures.md
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api import service
from api.replay_service import (
    InvalidReplayDate,
    InvalidReplayLoad,
    ReplayDataUnavailable,
    ReplayDateNotFound,
    available_replay_dates,
    committed_failures,
    committed_metrics,
    historical_replay,
)
from ml import config as C
from ml.features import build_features, model_inputs
from ml.recommend import recommend
from ml.train import MODEL_PATH

app = FastAPI(title="GridGreen", version="0.1")
# The Next.js page and the API docs call this API from the browser. Only pages served
# from this machine (localhost / 127.0.0.1, any port, e.g. 3001 when 3000 is busy) may
# read it. No credentials, so no cross-site write access is granted.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
_model = None


def model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise HTTPException(503, "model not trained yet: run `make train`")
        _model = joblib.load(MODEL_PATH)
    return _model


class PredictIn(BaseModel):
    history: list[float] = Field(..., description="168 hourly gCO2/kWh values, oldest first")
    load_kwh: float = Field(7.0, ge=0, description="flexible load to shift, e.g. EV charge")
    start_utc: datetime | None = Field(None, description="timestamp of history[0]; default now-168h")


@app.get("/health")
def health():
    return {"status": "ok", "region": C.REGION_NAME, "model_trained": MODEL_PATH.exists()}


@app.post("/predict")
def predict(body: PredictIn):
    if len(body.history) != 168:
        raise HTTPException(422, f"history must have exactly 168 values, got {len(body.history)}")
    if any(not np.isfinite(v) or v < 0 or v > 2000 for v in body.history):
        raise HTTPException(422, "history values must be finite and in 0..2000 gCO2/kWh")

    start = body.start_utc or (datetime.now(timezone.utc) - timedelta(hours=168))
    ts = pd.date_range(start, periods=168, freq="h", tz="UTC")
    df = pd.DataFrame({C.TS_COL: ts, C.CI_COL: body.history})

    # build_features drops rows without a known target; we only need the inputs, so we
    # append 24 placeholder hours and keep the last 24 feature rows.
    pad = pd.DataFrame({C.TS_COL: pd.date_range(ts[-1] + pd.Timedelta(hours=1), periods=24,
                                                freq="h", tz="UTC"), C.CI_COL: np.nan})
    feat = build_features(pd.concat([df, pad], ignore_index=True).assign(
        **{C.CI_COL: lambda d: d[C.CI_COL].ffill()}))
    feat = feat.tail(24)
    preds = model().predict(model_inputs(model(), feat))
    out = recommend(list(preds), body.load_kwh)
    out["forecast_start_utc"] = (ts[-1] + pd.Timedelta(hours=1)).isoformat()
    return out


# --- Historical replay over committed held-out predictions ---------------------------
# Read-only: these routes never retrain and never call a model. They must not be
# presented as live or prospective forecasts (see docs/ui/api_contract.md).


@app.get("/api/replay/dates")
def replay_dates():
    try:
        return {"dates_utc": available_replay_dates()}
    except ReplayDataUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/api/replay")
def replay(date: str, load_kwh: float = 7):
    try:
        return historical_replay(date, load_kwh)
    except (InvalidReplayDate, InvalidReplayLoad) as exc:
        raise HTTPException(422, str(exc)) from exc
    except ReplayDateNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except ReplayDataUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/api/replay/metrics")
def replay_metrics():
    try:
        return committed_metrics()
    except ReplayDataUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/api/replay/failures")
def replay_failures():
    try:
        return committed_failures()
    except ReplayDataUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


# --- Read-only routes for the web page (web/). Logic lives in api/service.py. --------


@app.get("/api/forecast")
def api_forecast(load_kwh: float = Query(7.0, ge=0, le=200, description="load to shift, kWh")):
    return service.forecast(load_kwh)


@app.get("/api/metrics")
def api_metrics():
    return service.metrics()


@app.get("/api/failures")
def api_failures():
    return service.failures()


@app.get("/api/history")
def api_history(days: int = Query(7, ge=1, le=30, description="days of past data")):
    return service.history(days)
