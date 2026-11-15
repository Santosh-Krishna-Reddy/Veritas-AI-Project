"""Pull EXTRA hourly columns out of the EIA-930 balance files we already downloaded.

Why: our model ties persistence on picking the cleanest hours, and the worst days were
wind-driven. These columns were in the files all along but `ml/fetch.py` never read them:
  PJM : demand_forecast_mw (EIA day-ahead forecast), net_generation_mw, total_interchange_mw
  MISO: miso_demand_mw, miso_wind_share, miso_coal_share, miso_gas_share
MISO is PJM's western neighbour. Weather moves west to east, so MISO's wind today MIGHT
lead PJM's wind tomorrow. That is a hypothesis for the model to test, not a claim.

Run:  python -m ml.fetch_grid_extra          -> data/raw/extra/grid_extra_PJM.csv
      python -m ml.fetch_grid_extra --crosscheck PATH/TO/PJM.xlsx -> results/ci_crosscheck.json
No network: reads data/raw/eia_cache/ (filled by `make fetch`). When each column becomes
known is written down in data/raw/extra/README.md.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from ml import config as C
from ml.fetch import UTC_COL, carbon_intensity, read_balance

OUT_PATH = C.RAW_DIR / "extra" / f"grid_extra_{C.EIA_BALANCING_AUTHORITY}.csv"
NEIGHBOUR_BA = "MISO"
MIN_COVERAGE = 0.95
# Sane-range checks (MW). PJM's peak demand is ~150 GW, MISO's ~130 GW; interchange is a
# few tens of GW at most. Anything outside these bounds means we read the wrong column.
MW_RANGE = (0, 250_000)
INTERCHANGE_RANGE = (-60_000, 60_000)
CROSSCHECK_PATH = C.ROOT / "results" / "ci_crosscheck.json"
EIA_XLSX_URL = "https://www.eia.gov/electricity/gridmonitor/knownissues/xls/PJM.xlsx"


def pick_column(columns: list[str], must: list[str], must_not: tuple[str, ...] = ()) -> str:
    """Return the ONE column whose lower-case name contains every word in `must` and none in
    `must_not`. EIA renames columns between years, so we match keywords like fetch.fuel_group()."""
    hits = [c for c in columns
            if all(w in c.lower() for w in must) and not any(w in c.lower() for w in must_not)]
    if len(hits) != 1:
        sys.exit(f"Expected one column matching {must} (not {must_not}), found {hits}")
    return hits[0]


def pjm_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Raw PJM EIA rows -> timestamp, demand_forecast_mw, net_generation_mw, total_interchange_mw."""
    cols = list(df.columns)
    wanted = {
        # EIA publishes no "(Adjusted)" version of the forecast, so we take the only one.
        "demand_forecast_mw": pick_column(cols, ["demand forecast"]),
        # Total net generation, not one fuel ("... from Coal" etc. are excluded).
        "net_generation_mw": pick_column(cols, ["net generation", "(adjusted)"], (" from ",)),
        "total_interchange_mw": pick_column(cols, ["total interchange", "(adjusted)"]),
    }
    out = pd.DataFrame()
    # Same parsing as ml/fetch.py: EIA stamps each hour at its END, in UTC.
    out[C.TS_COL] = pd.to_datetime(df[UTC_COL], format="%m/%d/%Y %I:%M:%S %p", utc=True)
    for name, col in wanted.items():
        # errors="coerce": the padded empty future hours become NaN, never 0.
        out[name] = pd.to_numeric(df[col], errors="coerce").values
    return out.dropna(subset=[C.TS_COL])


def miso_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Raw MISO EIA rows -> timestamp + miso_demand_mw and fuel shares, reusing fetch.carbon_intensity()."""
    ci = carbon_intensity(df)
    keep = {"demand_mw": "miso_demand_mw", "wind_share": "miso_wind_share",
            "coal_share": "miso_coal_share", "gas_share": "miso_gas_share"}
    return ci[[C.TS_COL, *keep]].rename(columns=keep)


def build(cache_dir: Path) -> pd.DataFrame:
    """Read every cached balance file once per region and return one hourly frame (outer join)."""
    files = sorted(cache_dir.glob("EIA930_BALANCE_*.csv"))  # Jan_Jun sorts before Jul_Dec
    if not files:
        sys.exit(f"No EIA files in {cache_dir}. Run `make fetch` first.")
    pjm, miso = [], []
    for path in files:
        print(f"read     {path.name}")
        pjm.append(pjm_columns(read_balance(path, C.EIA_BALANCING_AUTHORITY)))
        miso.append(miso_columns(read_balance(path, NEIGHBOUR_BA)))
    df = pd.concat(pjm).merge(pd.concat(miso), on=C.TS_COL, how="outer")
    return df.sort_values(C.TS_COL).reset_index(drop=True)


def validate(df: pd.DataFrame) -> dict[str, float]:
    """Fail fast on duplicate/irregular timestamps, low coverage or out-of-range values.
    Returns the share of hours that have a value, per column."""
    ts = df[C.TS_COL]
    assert ts.is_unique, "duplicate timestamps"
    assert (ts.diff().dropna() == pd.Timedelta(hours=1)).all(), "timestamps are not strictly hourly"
    coverage = {c: float(df[c].notna().mean()) for c in df.columns if c != C.TS_COL}
    low = {c: f"{v:.1%}" for c, v in coverage.items() if v < MIN_COVERAGE}
    assert not low, f"columns below {MIN_COVERAGE:.0%} coverage: {low}"
    for c in ("demand_forecast_mw", "net_generation_mw", "miso_demand_mw"):
        assert df[c].dropna().between(*MW_RANGE).all(), f"{c} outside {MW_RANGE}"
    assert df["total_interchange_mw"].dropna().between(*INTERCHANGE_RANGE).all(), "interchange range"
    for c in ("miso_wind_share", "miso_coal_share", "miso_gas_share"):
        assert df[c].dropna().between(0, 1).all(), f"{c} outside 0..1"
    return coverage


def main() -> None:
    df = build(C.EIA_CACHE_DIR)
    coverage = validate(df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.round({c: 5 for c in coverage}).to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}\n  {len(df)} hourly rows, "
          f"{df[C.TS_COL].min():%Y-%m-%d %H:%M} -> {df[C.TS_COL].max():%Y-%m-%d %H:%M} UTC")
    for col, share in coverage.items():
        s = df[col]
        print(f"  {col:22s} coverage {share:6.1%}  min {s.min():10.3f}  max {s.max():10.3f}")


# ---------------------------------------------------------------------------------------
# One-off cross-check: is our emission-factor carbon intensity close to EIA's own estimate?
# EIA's per-BA Excel file carries its hourly CO2 estimate (metric tons). Not part of
# `make`: it needs a 115 MB manual download and the openpyxl library.
# ---------------------------------------------------------------------------------------
def read_eia_co2(xlsx: Path) -> pd.DataFrame:
    """EIA PJM.xlsx -> timestamp, eia_co2_t, eia_net_gen_mw for 2024 onward (streams the sheet)."""
    import openpyxl  # only this one-off step needs it

    ws = openpyxl.load_workbook(xlsx, read_only=True)["Published Hourly Data"]
    rows = ws.iter_rows(values_only=True)
    head = list(next(rows))
    i_ts, i_co2 = head.index("UTC time"), head.index("CO2 Emissions Generated")
    i_ng = head.index("Adjusted net generation")
    start = pd.Timestamp(C.FETCH_START_YEAR, 1, 1)
    keep = [(r[i_ts], r[i_co2], r[i_ng]) for r in rows if r[i_ts] is not None and r[i_ts] >= start]
    out = pd.DataFrame(keep, columns=[C.TS_COL, "eia_co2_t", "eia_net_gen_mw"])
    out[C.TS_COL] = pd.to_datetime(out[C.TS_COL]).dt.tz_localize("UTC")
    for c in ("eia_co2_t", "eia_net_gen_mw"):
        out[c] = pd.to_numeric(out[c], errors="coerce")  # blank cells -> NaN, never 0
    return out


def crosscheck(xlsx: Path) -> dict:
    """Compare EIA_CO2 / net generation with our carbon_intensity on TRAIN hours only."""
    eia = read_eia_co2(xlsx)
    ours = pd.read_csv(C.RAW_DIR / f"gridgreen_{C.EIA_BALANCING_AUTHORITY}.csv",
                       usecols=[C.TS_COL, C.CI_COL], parse_dates=[C.TS_COL])
    extra = pd.read_csv(OUT_PATH, usecols=[C.TS_COL, "net_generation_mw"], parse_dates=[C.TS_COL])
    df = ours.merge(eia, on=C.TS_COL).merge(extra, on=C.TS_COL)
    # Test period is never looked at, not even for a data-quality check.
    df = df[df[C.TS_COL] < pd.Timestamp(C.SPLIT_DATE, tz="UTC")]
    # Same hour in both files? Then EIA's net generation equals the one we parsed from the CSV.
    ts_match = float((df["eia_net_gen_mw"] - df["net_generation_mw"]).abs().lt(1).mean())
    # metric tons / MWh  x 1e6 g/t  / 1e3 kWh/MWh  =  x 1000  -> g/kWh
    df["eia_ci"] = 1000 * df["eia_co2_t"] / df["net_generation_mw"]
    df = df.dropna(subset=["eia_ci", C.CI_COL])
    diff = df[C.CI_COL] - df["eia_ci"]
    return {
        "what": "our carbon_intensity vs EIA 'CO2 Emissions Generated' / Adjusted net generation, PJM",
        "eia_file_url": EIA_XLSX_URL, "eia_sheet": "Published Hourly Data",
        "download_date": date.today().isoformat(),
        "hours_compared": int(len(df)),
        "period_utc": [f"{df[C.TS_COL].min():%Y-%m-%d %H:%M}", f"{df[C.TS_COL].max():%Y-%m-%d %H:%M}"],
        "restricted_to_before": C.SPLIT_DATE,
        "timestamp_alignment_share": round(ts_match, 4),
        "eia_ci_mean_g_per_kwh": round(float(df["eia_ci"].mean()), 2),
        "our_ci_mean_g_per_kwh": round(float(df[C.CI_COL].mean()), 2),
        "pearson_correlation": round(float(df[C.CI_COL].corr(df["eia_ci"])), 4),
        "mean_bias_ours_minus_eia": round(float(diff.mean()), 2),
        "mae_g_per_kwh": round(float(diff.abs().mean()), 2),
        "likely_reason_for_bias": (
            "EIA uses PJM-fleet emission factors (same file, columns 'CO2 Factor: COL/NG': "
            "about 2.21 and 0.86 lb CO2/kWh in 2024-2026); we use 2023 national averages "
            "(2.31 and 0.96). Our gas factor is ~11% higher and gas is ~40% of PJM generation."
        ),
    }


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--crosscheck":
        result = crosscheck(Path(sys.argv[2]))
        CROSSCHECK_PATH.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
    else:
        main()
