"""Parser tests for ml/fetch.py using the two REAL EIA-930 header layouts (2024 and 2026).
No network: the rows below are tiny hand-made samples in the real file format."""

import io

import pandas as pd
import pytest

from ml import config as C
from ml.fetch import carbon_intensity, fuel_group, half_year_files

OLD_SOURCES = ["Coal", "Natural Gas", "Nuclear", "All Petroleum Products",
               "Hydropower and Pumped Storage", "Solar", "Wind", "Other Fuel Sources",
               "Unknown Fuel Sources"]
NEW_SOURCES = ["Coal", "Natural Gas", "Nuclear", "All Petroleum Products",
               "Hydropower Excluding Pumped Storage", "Pumped Storage",
               "Solar without Integrated Battery Storage", "Solar with Integrated Battery Storage",
               "Wind without Integrated Battery Storage", "Wind with Integrated Battery Storage",
               "Battery Storage", "Other Energy Storage", "Unknown Energy Storage",
               "Geothermal", "Other Fuel Sources", "Unknown Fuel Sources"]


def make_csv(sources: list[str], gen: dict[str, float]) -> pd.DataFrame:
    head = ["Balancing Authority", "UTC Time at End of Hour", "Demand (MW)"]
    head += [f"Net Generation (MW) from {s} (Adjusted)" for s in sources]
    row = ["PJM", "01/01/2026 7:00:00 AM", "90000"] + [str(gen.get(s, "")) for s in sources]
    text = ",".join(f'"{h}"' for h in head) + "\n" + ",".join(row) + "\n"
    return pd.read_csv(io.StringIO(text), thousands=",")


def test_fuel_groups_cover_both_layouts():
    for s in OLD_SOURCES + NEW_SOURCES:
        assert fuel_group(s) != "unknown" or "Unknown Fuel" in s, s
    assert fuel_group("Solar with Integrated Battery Storage") == "solar"
    assert fuel_group("Pumped Storage") == "storage"
    assert fuel_group("Hydropower and Pumped Storage") == "hydro"


@pytest.mark.parametrize("sources", [OLD_SOURCES, NEW_SOURCES])
def test_carbon_intensity_hand_checked(sources):
    # 25% coal, 25% gas, 50% nuclear -> 0.25*1048 + 0.25*435 = 370.75 g/kWh
    out = carbon_intensity(make_csv(sources, {"Coal": 1000, "Natural Gas": 1000, "Nuclear": 2000}))
    ef = C.EMISSION_FACTORS_G_PER_KWH
    assert out[C.CI_COL].iloc[0] == pytest.approx(0.25 * ef["coal"] + 0.25 * ef["gas"])
    assert out["coal_share"].iloc[0] == pytest.approx(0.25)
    assert out[C.TS_COL].iloc[0] == pd.Timestamp("2026-01-01 07:00", tz="UTC")


def test_storage_charging_does_not_go_negative():
    out = carbon_intensity(make_csv(NEW_SOURCES, {"Coal": 500, "Natural Gas": 500, "Battery Storage": -900}))
    assert out[C.CI_COL].iloc[0] == pytest.approx((1048 + 435) / 2)


def test_half_year_files():
    from datetime import date
    assert half_year_files(2025, date(2026, 11, 14)) == [
        (2025, "Jan_Jun"), (2025, "Jul_Dec"), (2026, "Jan_Jun"), (2026, "Jul_Dec")]
    assert half_year_files(2026, date(2026, 3, 1)) == [(2026, "Jan_Jun")]


def test_real_pjm_row_2026_07_01():
    """A real PJM row copied from EIA930_BALANCE_2026_Jul_Dec.csv (first hour of July 2026),
    including EIA's own header typo ('Solar witho ...') and double space ('Pumped Storage  ')."""
    sources = NEW_SOURCES.copy()
    sources[sources.index("Pumped Storage")] = "Pumped Storage "
    sources[sources.index("Solar with Integrated Battery Storage")] = "Solar witho Integrated Battery Storage"
    gen = {"Coal": 26989, "Natural Gas": 55250, "Nuclear": 32542, "All Petroleum Products": 1082,
           "Hydropower Excluding Pumped Storage": 508, "Other Fuel Sources": 3403,
           "Solar without Integrated Battery Storage": 75, "Wind without Integrated Battery Storage": 5442}
    df = make_csv(sources, gen)
    df["UTC Time at End of Hour"] = "07/01/2026 5:00:00 AM"
    out = carbon_intensity(df)
    ef = C.EMISSION_FACTORS_G_PER_KWH
    total = sum(gen.values())
    expected = (26989 * ef["coal"] + 55250 * ef["gas"] + 1082 * ef["oil"] + 3403 * ef["other"]) / total
    assert out[C.CI_COL].iloc[0] == pytest.approx(expected)
    assert 350 < expected < 550   # sanity: a coal+gas heavy summer night in PJM
    assert out["nuclear_share"].iloc[0] == pytest.approx(32542 / total)


def test_unreported_future_hours_are_empty_not_zero():
    """EIA pads the current file with empty rows up to the end of the day. Those must become
    missing values (dropped later), never a fake 0 gCO2/kWh."""
    out = carbon_intensity(make_csv(NEW_SOURCES, {}))
    assert out[C.CI_COL].isna().all()
