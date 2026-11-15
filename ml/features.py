"""Turn the hourly series into (features, target) rows for a 24-hour-ahead forecast.

For each hour t we predict carbon intensity at t + 24h using ONLY data at or before t:
  - ci_lag_0 .. ci_lag_23  : the last 24 hours (today's shape)
  - ci_lastweek            : value at t - 144h, i.e. same hour as the target, one week ago
  - target_hour, target_weekday, target_month : calendar features of the target time
  - x_<name>               : fuel mix + weather observed AT time t (config.EXTRA_COLS).
                             We do NOT use tomorrow's actual weather: at forecast time
                             nobody knows it, so using it would be leakage.
"""

from __future__ import annotations

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from ml import config as C

TARGET_COL = "target"
TARGET_TS_COL = "target_timestamp"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a new frame with one row per hour t that has full history and a known target."""
    s = df.set_index(C.TS_COL)[C.CI_COL].sort_index()
    out = pd.DataFrame(index=s.index)
    for lag in range(C.LAG_HOURS):
        out[f"ci_lag_{lag}"] = s.shift(lag)
    out["ci_lastweek"] = s.shift(C.LAST_WEEK_LAG)

    target_ts = s.index + pd.Timedelta(hours=C.HORIZON_HOURS)
    out[TARGET_TS_COL] = target_ts
    out["target_hour"] = target_ts.hour
    out["target_weekday"] = target_ts.weekday
    out["target_month"] = target_ts.month
    out[TARGET_COL] = s.shift(-C.HORIZON_HOURS).values

    # Fuel mix and weather observed at time t. Only columns present in the data are added
    # (synthetic data has none). The saved model remembers its own feature list, so
    # predict code reindexes to it -- see model_inputs().
    extra = df.set_index(C.TS_COL).sort_index()
    for col in C.EXTRA_COLS:
        if col in extra.columns:
            out[f"x_{col}"] = extra[col]

    # Drop rows lacking carbon-intensity history or a target; empty extras are allowed.
    need = [c for c in out.columns if not c.startswith("x_")]
    out = out.dropna(subset=need).rename_axis(C.TS_COL).reset_index()
    return out


def add_g2_features(feat: pd.DataFrame) -> pd.DataFrame:
    """Add target-day calendar facts that are known before the forecast is issued."""
    out = feat.copy()
    local = out[TARGET_TS_COL].dt.tz_convert(C.LOCAL_TIMEZONE)
    local_dates = local.dt.tz_localize(None).dt.normalize()
    holidays = USFederalHolidayCalendar().holidays(
        start=local_dates.min(), end=local_dates.max()
    )
    out["target_local_hour"] = local.dt.hour
    out["target_weekend"] = (local.dt.day_of_week >= 5).astype(int)
    out["target_holiday"] = local_dates.isin(holidays).astype(int)
    return out


def build_ladder_features(df: pd.DataFrame, group: str) -> pd.DataFrame:
    """Build the available G0-G2 ladder while preserving build_features' public API."""
    if group not in {"G0", "G1", "G2"}:
        raise ValueError(f"unsupported feature group without extra data: {group}")
    feat = build_features(df)
    return add_g2_features(feat) if group == "G2" else feat


def lag_only_columns(df: pd.DataFrame) -> list[str]:
    """Feature columns WITHOUT fuel mix / weather. Used to measure what the extras add."""
    return [c for c in feature_columns(df) if not c.startswith("x_")]


def feature_columns(df: pd.DataFrame) -> list[str]:
    """Every column that is an input to the model (not timestamps, not the target)."""
    return [c for c in df.columns if c not in (C.TS_COL, TARGET_TS_COL, TARGET_COL)]


def restrict_to_period(feat: pd.DataFrame, start=None, end=None) -> pd.DataFrame:
    """Keep rows whose TARGET time falls in [start, end). Used to avoid leakage at the split:
    a train row whose target is after SPLIT_DATE would peek into the test period."""
    m = pd.Series(True, index=feat.index)
    if start is not None:
        m &= feat[TARGET_TS_COL] >= pd.Timestamp(start, tz="UTC")
    if end is not None:
        m &= feat[TARGET_TS_COL] < pd.Timestamp(end, tz="UTC")
    return feat[m].reset_index(drop=True)


def model_inputs(model, feat: pd.DataFrame) -> pd.DataFrame:
    """Columns in the exact order the trained model expects. Any feature the model was
    trained on but that is missing here (e.g. weather in an API call) becomes NaN, which
    gradient boosting treats as 'unknown' instead of crashing."""
    return feat.reindex(columns=list(model.feature_names_in_))
