"""Turn the hourly series into (features, target) rows for a 24-hour-ahead forecast.

For each hour t we predict carbon intensity at t + 24h using ONLY data at or before t:
  - ci_lag_0 .. ci_lag_23  : the last 24 hours (today's shape)
  - ci_lastweek            : value at t - 144h, i.e. same hour as the target, one week ago
  - target_hour, target_weekday, target_month : calendar features of the target time
"""

from __future__ import annotations

import pandas as pd

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

    out = out.dropna().rename_axis(C.TS_COL).reset_index()
    return out


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
