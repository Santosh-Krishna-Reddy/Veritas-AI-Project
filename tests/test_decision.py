"""Focused, offline decision audit tests; no network or EIA cache required."""
import numpy as np
import pandas as pd

from ml.decision import calculate, full_days, one_day


def test_regret_nonnegative_and_oracle_zero():
    time = pd.date_range("2026-08-01", periods=24, freq="h", tz="UTC")
    data = pd.DataFrame({
        "target_timestamp": time,
        "target": np.arange(24, dtype=float),
        "pred_model": np.arange(24, dtype=float),
        "pred_persistence": np.arange(23, -1, -1, dtype=float),
    })
    model = one_day(data, "pred_model", 3)
    baseline = one_day(data, "pred_persistence", 3)
    assert model["regret_g_per_kwh"] == 0
    assert model["cleanest_k_overlap"] == 1
    assert baseline["regret_g_per_kwh"] > 0
    assert baseline["cleanest_k_overlap"] == 0
    assert len(full_days(data)) == 1
    result = calculate(data)
    assert result["full_utc_days"] == 1
    assert result["models"]["model"]["regret_g_per_kwh"] == 0


def test_partial_days_excluded():
    hours = pd.date_range("2026-08-01", periods=30, freq="h", tz="UTC")
    data = pd.DataFrame({"target_timestamp": hours})
    assert len(full_days(data)) == 1


def test_chicago_daylight_saving_counts_25_hours():
    hours = pd.date_range("2026-11-01 05:00", periods=25, freq="h", tz="UTC")
    data = pd.DataFrame({"target_timestamp": hours})
    assert len(full_days(data, "America/Chicago")) == 1
    assert len(full_days(data, "UTC")) == 0
