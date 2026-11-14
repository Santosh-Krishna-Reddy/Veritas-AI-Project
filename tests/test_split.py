"""Leakage tests. If any of these fail, every reported number is invalid."""

import pandas as pd

from ml import config as C
from ml.features import (TARGET_COL, TARGET_TS_COL, build_features,
                         feature_columns, restrict_to_period)


def test_split_no_leakage(split):
    train, test = split
    assert train[C.TS_COL].max() < test[C.TS_COL].min()
    assert not set(train[C.TS_COL]) & set(test[C.TS_COL])


def test_features_no_future(series, split_date):
    """No feature value may come from after the row's own timestamp, and train targets
    must all be before the split date."""
    feat = restrict_to_period(build_features(series), end=split_date)
    cut = pd.Timestamp(split_date, tz="UTC")
    assert (feat[TARGET_TS_COL] < cut).all()
    assert (feat[TARGET_TS_COL] == feat[C.TS_COL] + pd.Timedelta(hours=C.HORIZON_HOURS)).all()

    # Spot check: ci_lag_0 at time t equals the series at t; ci_lastweek equals t-144h.
    s = series.set_index(C.TS_COL)[C.CI_COL]
    row = feat.iloc[100]
    assert row["ci_lag_0"] == s[row[C.TS_COL]]
    assert row["ci_lastweek"] == s[row[C.TS_COL] - pd.Timedelta(hours=C.LAST_WEEK_LAG)]
    assert row[TARGET_COL] == s[row[C.TS_COL] + pd.Timedelta(hours=C.HORIZON_HOURS)]


def test_feature_columns_exclude_target(series):
    feat = build_features(series)
    cols = feature_columns(feat)
    assert TARGET_COL not in cols and TARGET_TS_COL not in cols and C.TS_COL not in cols
    assert len(cols) == C.LAG_HOURS + 1 + 3  # synthetic data has no fuel-mix/weather columns


def test_extra_columns_use_time_t_only(series):
    """Fuel mix / weather features must be the value AT time t, never at the target time."""
    df = series.assign(temp_c=range(len(series)))
    feat = build_features(df)
    row = feat.iloc[50]
    t_index = series.index[series[C.TS_COL] == row[C.TS_COL]][0]
    assert row["x_temp_c"] == t_index
