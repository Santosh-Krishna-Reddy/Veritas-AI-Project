"""One test per read-only web route (api/service.py). Skips when artefacts are missing."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from ml import config as C
from ml.train import MODEL_PATH

c = TestClient(app)
needs_data = pytest.mark.skipif(
    not (MODEL_PATH.exists() and (C.PROCESSED_DIR / "test.csv").exists()),
    reason="run `make data train` first")
needs_results = pytest.mark.skipif(
    not (C.RESULTS_DIR / "failure_features.csv").exists(), reason="run `make failures` first")


@needs_data
def test_forecast_returns_24_hours_and_3_cleanest():
    body = c.get("/api/forecast", params={"load_kwh": 7}).json()
    assert len(body["hours"]) == 24
    assert len(body["cleanest_hours"]) == 3
    assert body["co2_saved_kg"] >= 0
    # Per-hour savings agree with the headline: cleanest hour = headline, dirtiest = 0.
    by_ts = {x["ts_local"]: x["saved_kg"] for x in body["hours"]}
    assert by_ts[body["cleanest_hours"][0]] == pytest.approx(body["co2_saved_kg"], abs=1e-3)
    assert by_ts[body["dirtiest_hour"]] == 0
    # data_through is the last REAL hour; gap-filled hours after it are counted, not hidden.
    assert body["filled_hours"] >= 0
    h = body["hours"][0]
    assert h["ts_local"].endswith(("-05:00", "-06:00"))  # America/Chicago, CST or CDT


@pytest.mark.parametrize("bad", [-1, 201, "abc"])
def test_forecast_rejects_bad_load(bad):
    r = c.get("/api/forecast", params={"load_kwh": bad})
    assert r.status_code == 422


def test_metrics_has_model_and_persistence_and_verdict():
    body = c.get("/api/metrics").json()
    assert {"model", "persistence"} <= body["metrics"].keys()
    assert "persistence" in body["verdict"]


def test_verdict_follows_numbers():
    from api.service import verdict
    win = {"model": {"mae": 1, "cleanest_3_overlap": 0.6},
           "persistence": {"mae": 2, "cleanest_3_overlap": 0.4}}
    assert "beats persistence on picking" in verdict(win, None)
    tie = {"vs_persistence_day_by_day": {"model": {"bootstrap_95ci": [-0.05, 0.03]}}}
    assert "ties persistence" in verdict(win, tie)
    equal = {"model": {"mae": 1, "cleanest_3_overlap": 0.5},
             "persistence": {"mae": 2, "cleanest_3_overlap": 0.5}}
    assert "ties persistence" in verdict(equal, None)


def test_records_turns_nan_into_null():
    import json

    import pandas as pd

    from api.service import _records
    rows = _records(pd.DataFrame({"a": [1.0, float("nan")]}))
    assert json.loads(json.dumps(rows, allow_nan=False)) == [{"a": 1.0}, {"a": None}]


@needs_results
def test_failures_sorted_worst_first():
    days = c.get("/api/failures").json()["days"]
    assert days and len(days[0]["hours"]) == 24
    assert days[0]["model_mae"] >= days[-1]["model_mae"]
    assert days[0]["explanation"]


@needs_data
def test_history_length_and_bounds():
    assert len(c.get("/api/history", params={"days": 2}).json()["hours"]) == 48
    assert c.get("/api/history", params={"days": 0}).status_code == 422
    assert c.get("/api/history", params={"days": 31}).status_code == 422
