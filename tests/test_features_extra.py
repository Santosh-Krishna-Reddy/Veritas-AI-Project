"""Leakage checks for the feature groups available without wave-2 data files."""

import pandas as pd

from ml import config as C
from ml.features import TARGET_TS_COL, build_ladder_features
from ml.predict import latest_forecast


def test_observations_after_t_do_not_change_row_t(series):
    """Changing observed weather after origin t cannot change features at origin t."""
    source = series.assign(temp_c=range(len(series)))
    before = build_ladder_features(source, "G2")
    row = before.iloc[50]
    changed = source.copy()
    changed.loc[changed[C.TS_COL] > row[C.TS_COL], "temp_c"] = -9999
    after = build_ladder_features(changed, "G2")
    pd.testing.assert_series_equal(row, after.iloc[50])


def test_g2_uses_target_time_in_chicago(series):
    """Local hour and weekend flags describe the target, not the forecast origin."""
    feat = build_ladder_features(series, "G2")
    row = feat.iloc[100]
    local = row[TARGET_TS_COL].tz_convert(C.LOCAL_TIMEZONE)
    assert row["target_local_hour"] == local.hour
    assert row["target_weekend"] == int(local.day_of_week >= 5)


def test_g2_marks_us_federal_holiday():
    """July 4 is known in advance and is flagged using its Chicago calendar date."""
    timestamps = pd.date_range("2025-06-20", periods=500, freq="h", tz="UTC")
    source = pd.DataFrame({C.TS_COL: timestamps, C.CI_COL: range(len(timestamps))})
    feat = build_ladder_features(source, "G2")
    local = feat[TARGET_TS_COL].dt.tz_convert(C.LOCAL_TIMEZONE)
    july_four = feat[local.dt.strftime("%Y-%m-%d") == "2025-07-04"]
    assert not july_four.empty
    assert (july_four["target_holiday"] == 1).all()


def test_latest_forecast_returns_next_complete_day():
    """The selected model returns 24 ordered rows with usable interval bounds."""
    rows = latest_forecast()
    assert len(rows) == 24
    assert list(rows[0]) == ["timestamp", "forecast", "lo", "hi", "persistence"]
    assert all(row["lo"] <= row["forecast"] <= row["hi"] for row in rows)
    timestamps = pd.to_datetime([row["timestamp"] for row in rows], utc=True)
    assert (timestamps[1:] - timestamps[:-1] == pd.Timedelta(hours=1)).all()
