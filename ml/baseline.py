"""The simplest possible forecasts. The model must beat these or it adds nothing.

persistence : tomorrow's hour h = today's hour h          (ci_lag_0)
last_week   : tomorrow's hour h = same hour one week ago  (ci_lastweek)
"""

from __future__ import annotations

import pandas as pd


def persistence(feat: pd.DataFrame) -> pd.Series:
    """Predict the value observed 24 h before the target, i.e. 'tomorrow = today'."""
    return feat["ci_lag_0"].rename("pred_persistence")


def last_week(feat: pd.DataFrame) -> pd.Series:
    """Predict the value observed one week before the target."""
    return feat["ci_lastweek"].rename("pred_last_week")


BASELINES = {"persistence": persistence, "last_week": last_week}
