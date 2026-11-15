"""Smoke tests for ml/decision.py on tiny hand-made days (no files needed)."""

import numpy as np
import pandas as pd

from ml.decision import bootstrap_vs_persistence, day_scores, flat_bottom, full_days, summarize


def make_days(n_days: int = 3, start: str = "2026-08-01") -> pd.DataFrame:
    """n full UTC days with a known V-shaped truth: hour 12 is cleanest, hours 0/23 dirtiest."""
    ts = pd.date_range(start, periods=24 * n_days, freq="h", tz="UTC")
    truth = 300 + 5 * np.abs(ts.hour - 12)
    return pd.DataFrame({"target_timestamp": ts, "target": truth.astype(float),
                         "pred_model": truth + 7.0,             # right shape, wrong level
                         "pred_persistence": truth[::-1] * 1.0})  # reversed shape


def test_perfect_shape_has_zero_regret_and_full_capture():
    s = summarize(day_scores(full_days(make_days(), "UTC"), k=3))
    assert s["model"]["regret"] == 0 and s["model"]["overlap"] == 1
    assert np.isclose(s["model"]["captured"], 1.0)
    assert s["persistence"]["regret"] > 0 and s["persistence"]["overlap"] < 1


def test_partial_days_are_dropped_and_dst_day_kept():
    df = make_days(3).iloc[5:]  # first UTC day now has only 19 hours
    assert full_days(df, "UTC")["day"].nunique() == 2
    # Nov 1 2026 has 25 hours in Chicago (clocks go back); it must count as full.
    nov = make_days(3, start="2026-10-31 05:00")
    days = full_days(nov, "America/Chicago")
    assert days.groupby("day").size().max() == 25


def test_bootstrap_and_flat_bottom_are_finite():
    days = full_days(make_days(5), "UTC")
    boot = bootstrap_vs_persistence(day_scores(days, k=3))["model"]
    assert boot["ci95"][0] <= boot["mean_diff"] <= boot["ci95"][1]
    gap = flat_bottom(days)
    assert gap["median"] == 10.0  # cleanest 6: 300,305,305,310,310,315 -> 6th 315 - 3rd 305
