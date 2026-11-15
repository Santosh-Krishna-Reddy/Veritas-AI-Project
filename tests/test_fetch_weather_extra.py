"""No-network tests for ml/fetch_weather_extra.py: a tiny hand-made Open-Meteo response."""

import pandas as pd
import pytest

from ml import config as C
from ml.fetch_weather_extra import VARS, to_frame, validate, year_ranges
from datetime import date


def fake_response(suffix: str, temps: list) -> dict:
    """Same shape as a real Open-Meteo JSON reply (timezone=GMT), 3 hours long."""
    hourly = {"time": ["2024-03-01T00:00", "2024-03-01T01:00", "2024-03-01T02:00"]}
    hourly[f"temperature_2m{suffix}"] = temps
    hourly[f"wind_speed_100m{suffix}"] = [5.0, None, 7.5]     # None = hour the API lacks
    hourly[f"shortwave_radiation{suffix}"] = [0.0, 0.0, 12.0]
    hourly[f"cloud_cover{suffix}"] = [100, 50, 0]
    return {"hourly": hourly}


def test_forecast_columns_and_utc_timestamps():
    df = to_frame(fake_response("_previous_day1", [1.0, 2.0, 3.0]), "chicago",
                  "_previous_day1", "_fc1")
    assert list(df.columns) == [C.TS_COL] + [f"chicago_{v}_fc1" for v in VARS]
    assert str(df[C.TS_COL].dt.tz) == "UTC"
    assert df[C.TS_COL].iloc[0] == pd.Timestamp("2024-03-01 00:00", tz="UTC")
    assert pd.isna(df["chicago_wind_speed_100m_fc1"].iloc[1])     # missing stays missing


def test_validate_reports_coverage_and_rejects_bad_data():
    df = to_frame(fake_response("", [1.0, 2.0, 3.0]), "chicago", "", "")
    assert validate(df, "t")["chicago_wind_speed_100m"] == pytest.approx(2 / 3, abs=1e-3)
    hot = to_frame(fake_response("", [1.0, 2.0, 99.0]), "chicago", "", "")
    with pytest.raises(AssertionError, match="outside"):
        validate(hot, "t")
    with pytest.raises(AssertionError, match="duplicate"):
        validate(pd.concat([df, df.tail(1)]), "t")


def test_year_ranges_one_call_per_year():
    assert year_ranges(date(2024, 1, 1), date(2025, 3, 5)) == [
        (date(2024, 1, 1), date(2024, 12, 31)), (date(2025, 1, 1), date(2025, 3, 5))]
