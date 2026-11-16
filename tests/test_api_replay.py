"""Contract tests for the committed historical replay API."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api import service
from api.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_dates_include_only_complete_utc_days(client: TestClient):
    response = client.get("/api/replay/dates")

    assert response.status_code == 200, response.text
    dates = response.json()["dates_utc"]
    assert dates == sorted(dates)
    assert len(dates) == 105
    assert dates[0] == "2026-08-01"
    assert dates[-1] == "2026-11-13"
    assert "2026-11-14" not in dates


def test_replay_is_chronological_and_matches_committed_units(client: TestClient):
    response = client.get("/api/replay", params={"date": "2026-08-01", "load_kwh": 7})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "historical_replay"
    assert body["utc_day"] == "2026-08-01"
    assert body["display_timezone"] == "America/Chicago"
    assert len(body["hours"]) == 24

    timestamps = [datetime.fromisoformat(hour["ts_utc"]) for hour in body["hours"]]
    assert timestamps == sorted(timestamps)
    assert all(timestamp.date().isoformat() == "2026-08-01" for timestamp in timestamps)
    assert all(
        set(hour) == {"ts_utc", "ts_local", "forecast", "persistence", "observed"}
        for hour in body["hours"]
    )

    committed = pd.read_csv(service.PREDICTIONS_PATH)
    source = committed[committed["target_timestamp"].str.startswith("2026-08-01")]
    first = body["hours"][0]
    assert first["forecast"] == pytest.approx(source.iloc[0]["pred_model"])
    assert first["persistence"] == pytest.approx(source.iloc[0]["pred_persistence"])
    assert first["observed"] == pytest.approx(source.iloc[0]["target"])


def test_replay_recommendations_use_model_forecast(client: TestClient):
    body = client.get("/api/replay?date=2026-10-14&load_kwh=7").json()
    forecast = [hour["forecast"] for hour in body["hours"]]
    expected_cleanest = sorted(range(24), key=lambda index: (forecast[index], index))[:3]
    expected_dirtiest = max(range(24), key=lambda index: forecast[index])
    expected_difference = round(
        7 * (forecast[expected_dirtiest] - forecast[expected_cleanest[0]]) / 1000,
        3,
    )

    assert body["recommended_indices"] == expected_cleanest
    assert body["dirtiest_index"] == expected_dirtiest
    assert body["modeled_difference_kg"] == expected_difference
    assert "average-intensity" in body["disclaimer"]
    assert "not a live operational forecast" in body["disclaimer"]
    assert "not" in body["disclaimer"] and "marginal avoided emissions" in body["disclaimer"]


def test_replay_zero_load_has_zero_modeled_difference(client: TestClient):
    response = client.get("/api/replay?date=2026-08-01&load_kwh=0")

    assert response.status_code == 200
    assert response.json()["modeled_difference_kg"] == 0


@pytest.mark.parametrize("load", ["-0.01", "200.01", "nan", "inf"])
def test_replay_rejects_invalid_load(client: TestClient, load: str):
    response = client.get(f"/api/replay?date=2026-08-01&load_kwh={load}")

    assert response.status_code == 422
    assert "load_kwh" in response.text


def test_replay_rejects_invalid_or_unavailable_dates(client: TestClient):
    malformed = client.get("/api/replay?date=2026-8-1")
    unavailable = client.get("/api/replay?date=2026-11-14")

    assert malformed.status_code == 422
    assert "YYYY-MM-DD" in malformed.text
    assert unavailable.status_code == 404
    assert "no complete 24-hour historical replay" in unavailable.text


def test_replay_missing_required_file_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
):
    monkeypatch.setattr(service, "PREDICTIONS_PATH", tmp_path / "missing.csv")

    response = client.get("/api/replay/dates")

    assert response.status_code == 503
    assert "required replay data unavailable" in response.text


def test_metrics_return_committed_files_in_named_fields(client: TestClient):
    response = client.get("/api/metrics")

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"evaluation_metrics", "decision_metrics"}
    assert body["evaluation_metrics"]["_meta"]["region"].startswith("PJM")
    assert body["decision_metrics"]["source"] == "results/test_predictions.csv"


def test_metrics_missing_required_file_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
):
    monkeypatch.setattr(service, "METRICS_PATH", tmp_path / "missing.json")

    response = client.get("/api/metrics")

    assert response.status_code == 503
    assert "required metrics unavailable" in response.text


def test_failures_are_grounded_in_committed_report(client: TestClient):
    response = client.get("/api/failures")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "available"
    assert body["source"] == "results/failures.md"
    assert len(body["records"]) == 5
    assert body["records"][0] == {
        "utc_day": "2026-10-14",
        "weekday": "Wed",
        "model_mae_gco2_per_kwh": 30.0,
        "persistence_mae_gco2_per_kwh": 36.0,
        "average_observed_gco2_per_kwh": 411.0,
        "error_type": "level offset",
        "evidence": (
            "-30 g all day; temp_c 24 -> 19 (1.02x test avg); "
            "wind_share 6.4% -> 3.3% (1.16x test avg)"
        ),
    }


def test_failures_use_explicit_unavailable_state_without_evidence(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
):
    report = tmp_path / "failures.md"
    report.write_text("# No generated failure table\n", encoding="utf-8")
    monkeypatch.setattr(service, "FAILURES_PATH", report)

    response = client.get("/api/failures")

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert response.json()["records"] == []


def test_failures_missing_required_file_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path
):
    monkeypatch.setattr(service, "FAILURES_PATH", tmp_path / "missing.md")

    response = client.get("/api/failures")

    assert response.status_code == 503
    assert "required failure evidence unavailable" in response.text


def test_cors_allows_only_explicit_development_origins(client: TestClient):
    allowed = client.options(
        "/api/replay/dates",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    denied = client.options(
        "/api/replay/dates",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in denied.headers
