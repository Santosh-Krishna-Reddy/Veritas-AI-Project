"""Tests for ml/fetch_grid_extra.py. No network: a tiny sample in the REAL EIA-930 layout.
The first data row is the real PJM row for 07/01/2026 hour 1 (EIA930_BALANCE_2026_Jul_Dec)."""

import io

import pandas as pd
import pytest

from ml import config as C
from ml.fetch_grid_extra import pick_column, pjm_columns, validate

HEAD = ["Balancing Authority", "UTC Time at End of Hour", "Demand Forecast (MW)", "Demand (MW)",
        "Net Generation (MW)", "Total Interchange (MW)", "Net Generation (MW) (Imputed)",
        "Demand (MW) (Adjusted)", "Net Generation (MW) (Adjusted)",
        "Total Interchange (MW) (Adjusted)", "Net Generation (MW) from Coal (Adjusted)"]
ROWS = [
    ["PJM", "07/01/2026 5:00:00 AM", "106285", "117267", "124208", "7333", "",
     "117267", "124208", "7333", "26989"],
    # Padded future hour: EIA leaves every value blank. It must become NaN, never 0.
    ["PJM", "07/01/2026 6:00:00 AM", "", "", "", "", "", "", "", "", ""],
]


def sample() -> pd.DataFrame:
    text = ",".join(f'"{h}"' for h in HEAD) + "\n" + "\n".join(",".join(r) for r in ROWS)
    return pd.read_csv(io.StringIO(text), thousands=",")


def test_pjm_columns_real_row_and_empty_hour():
    out = pjm_columns(sample())
    assert out[C.TS_COL].iloc[0] == pd.Timestamp("2026-07-01 05:00", tz="UTC")
    assert out.iloc[0][["demand_forecast_mw", "net_generation_mw", "total_interchange_mw"]].tolist() \
        == [106285, 124208, 7333]
    assert out.iloc[1].drop(C.TS_COL).isna().all()


def test_pick_column_excludes_by_fuel_and_fails_on_ambiguity():
    assert pick_column(HEAD, ["net generation", "(adjusted)"], (" from ",)) \
        == "Net Generation (MW) (Adjusted)"
    with pytest.raises(SystemExit):
        pick_column(HEAD, ["net generation"])  # 4 matches: must refuse to guess


def good_frame(hours: int = 48) -> pd.DataFrame:
    ts = pd.date_range("2026-01-01", periods=hours, freq="h", tz="UTC")
    df = pd.DataFrame({C.TS_COL: ts, "demand_forecast_mw": 90_000.0, "net_generation_mw": 95_000.0,
                       "total_interchange_mw": 5_000.0, "miso_demand_mw": 70_000.0,
                       "miso_wind_share": 0.2, "miso_coal_share": 0.3, "miso_gas_share": 0.4})
    return df


def test_validate_accepts_good_and_rejects_bad():
    assert validate(good_frame())["net_generation_mw"] == 1.0
    dup = pd.concat([good_frame(), good_frame().tail(1)], ignore_index=True)
    bad_share = good_frame().assign(miso_wind_share=1.5)
    sparse = good_frame().assign(net_generation_mw=float("nan"))
    for bad in (dup, bad_share, sparse):
        with pytest.raises(AssertionError):
            validate(bad)
