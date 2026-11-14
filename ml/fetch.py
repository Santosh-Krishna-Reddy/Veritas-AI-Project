"""Download REAL public data and write one tidy hourly CSV to data/raw/.

Sources (both free, no API key, cited in CREDITS.md):
  1. EIA-930 Hourly Electric Grid Monitor "balance" files: hourly generation by fuel for
     every US balancing authority. We keep ours (config.EIA_BALANCING_AUTHORITY) and
     compute carbon intensity = sum(generation_by_fuel x emission factor) / total generation.
  2. Open-Meteo historical weather API: hourly temperature, wind, solar radiation, cloud.

Run:  python -m ml.fetch      (or: make fetch)   then: make data
Output: data/raw/gridgreen_<BA>.csv with columns
        timestamp (UTC, end of hour), carbon_intensity (gCO2/kWh), demand_mw,
        coal_share .. solar_share (0..1), temp_c, wind_ms, solar_wm2, cloud_pct
"""

from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from ml import config as C

BA_COL = "Balancing Authority"
UTC_COL = "UTC Time at End of Hour"
DEMAND_COL = "Demand (MW)"
# e.g. "Net Generation (MW) from Natural Gas (Adjusted)" -> group 1 = "Natural Gas"
GEN_RE = re.compile(r"^Net Generation \(MW\) from (.+?)\s+\(Adjusted\)$")


def fuel_group(source_name: str) -> str:
    """Map an EIA energy-source label to one of our groups. EIA renamed and split its
    categories in 2024-25 (e.g. 'Solar' -> 'Solar with/without Integrated Battery
    Storage'), so we match on keywords instead of exact names."""
    s = source_name.lower()
    if "coal" in s:
        return "coal"
    if "natural gas" in s:
        return "gas"
    if "petroleum" in s:
        return "oil"
    if "nuclear" in s:
        return "nuclear"
    if "storage" in s and "solar" not in s and "wind" not in s and "hydro" not in s:
        return "storage"          # batteries / pumped storage: not a generation source
    if "solar" in s:
        return "solar"
    if "wind" in s:
        return "wind"
    if "hydro" in s:
        return "hydro"
    if "geothermal" in s:
        return "geothermal"
    if "other" in s:
        return "other"
    return "unknown"


def half_year_files(start_year: int, today: date) -> list[tuple[int, str]]:
    """Every (year, 'Jan_Jun' | 'Jul_Dec') from start_year up to the half containing today."""
    out = []
    for year in range(start_year, today.year + 1):
        out.append((year, "Jan_Jun"))
        if year < today.year or today.month >= 7:
            out.append((year, "Jul_Dec"))
    return out


def download(url: str, dest: Path, refresh: bool) -> Path:
    """Stream a file to disk. Finished half-years are cached; the current one is refreshed."""
    if dest.exists() and not refresh:
        print(f"cached   {dest.name}")
        return dest
    print(f"download {url}")
    with requests.get(url, stream=True, timeout=120) as r:
        if r.status_code != 200:
            sys.exit(f"EIA download failed ({r.status_code}) for {url}")
        tmp = dest.with_suffix(".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        tmp.replace(dest)
    return dest


def read_balance(path: Path, ba: str) -> pd.DataFrame:
    """Read one EIA balance file in chunks (they are large) and keep only our region's rows."""
    parts = []
    for chunk in pd.read_csv(path, chunksize=200_000, thousands=",", low_memory=False):
        parts.append(chunk[chunk[BA_COL] == ba])
    df = pd.concat(parts, ignore_index=True)
    if df.empty:
        sys.exit(f"No rows for balancing authority {ba!r} in {path.name}. Check config.")
    return df


def carbon_intensity(df: pd.DataFrame) -> pd.DataFrame:
    """Turn raw EIA rows into: timestamp, carbon_intensity, demand_mw, fuel shares.
    Returns a new frame; fails loudly if the expected columns are missing."""
    gen_cols = {c: fuel_group(m.group(1)) for c in df.columns if (m := GEN_RE.match(c))}
    groups = set(gen_cols.values())
    if not {"coal", "gas"} <= groups or UTC_COL not in df.columns:
        sys.exit(f"EIA file layout changed. Columns found: {list(df.columns)}")

    out = pd.DataFrame()
    out[C.TS_COL] = pd.to_datetime(df[UTC_COL], format="%m/%d/%Y %I:%M:%S %p", utc=True)
    out["demand_mw"] = pd.to_numeric(df[DEMAND_COL], errors="coerce").values

    # MW generated per group this hour. Negative values (station use, storage charging)
    # are clipped to 0 so they cannot make the intensity negative.
    by_group = pd.DataFrame(index=df.index)
    for group in sorted(groups):
        cols = [c for c, g in gen_cols.items() if g == group]
        by_group[group] = df[cols].apply(pd.to_numeric, errors="coerce").fillna(0).clip(lower=0).sum(axis=1)
    by_group = by_group.drop(columns=["storage"], errors="ignore")
    total = by_group.sum(axis=1)

    grams = sum(by_group[g] * ef for g, ef in C.EMISSION_FACTORS_G_PER_KWH.items() if g in by_group)
    out[C.CI_COL] = (grams / total).where(total > 0).values   # empty when nothing reported
    for g in ("coal", "gas", "nuclear", "wind", "solar"):
        share = by_group[g] / total if g in by_group else float("nan")
        out[f"{g}_share"] = pd.Series(share, index=df.index).where(total > 0).values
    return out.dropna(subset=[C.TS_COL])


def fetch_grid(today: date) -> pd.DataFrame:
    """Download every half-year file since FETCH_START_YEAR and return one hourly frame."""
    C.EIA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    files = half_year_files(C.FETCH_START_YEAR, today)
    frames = []
    for i, (year, half) in enumerate(files):
        url = C.EIA_BALANCE_URL.format(year=year, half=half)
        path = download(url, C.EIA_CACHE_DIR / f"EIA930_BALANCE_{year}_{half}.csv",
                        refresh=(i == len(files) - 1))
        frames.append(carbon_intensity(read_balance(path, C.EIA_BALANCING_AUTHORITY)))
    grid = pd.concat(frames, ignore_index=True)
    return grid.sort_values(C.TS_COL).drop_duplicates(C.TS_COL).reset_index(drop=True)


def fetch_weather(start: date, end: date) -> pd.DataFrame:
    """Hourly weather in UTC for the region's reference point. The archive lags ~5 days;
    hours it does not have yet simply stay empty after the merge."""
    params = {
        "latitude": C.WEATHER_LAT, "longitude": C.WEATHER_LON,
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "hourly": ",".join(C.WEATHER_VARS), "timezone": "GMT", "wind_speed_unit": "ms",
    }
    print(f"download {C.OPEN_METEO_URL} ({start} -> {end})")
    r = requests.get(C.OPEN_METEO_URL, params=params, timeout=120)
    if r.status_code != 200:
        sys.exit(f"Open-Meteo failed ({r.status_code}): {r.text[:300]}")
    hourly = r.json().get("hourly")
    if not hourly or "time" not in hourly:
        sys.exit(f"Open-Meteo response has no hourly data: {r.text[:300]}")
    w = pd.DataFrame(hourly).rename(columns=C.WEATHER_VARS)
    w[C.TS_COL] = pd.to_datetime(w.pop("time"), utc=True)
    return w


def main() -> None:
    today = date.today()
    grid = fetch_grid(today)
    start = grid[C.TS_COL].min().date()
    weather = fetch_weather(start, today - timedelta(days=1))
    df = grid.merge(weather, on=C.TS_COL, how="left")

    # Validate at the boundary before anything downstream trusts this file.
    ci = df[C.CI_COL]
    assert ci.notna().mean() > 0.95, f"only {ci.notna().mean():.0%} of hours have carbon intensity"
    assert ci.dropna().between(0, 1200).all(), "carbon intensity outside 0..1200 g/kWh"

    C.RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = C.RAW_DIR / f"gridgreen_{C.EIA_BALANCING_AUTHORITY}.csv"
    df.to_csv(out, index=False)
    print(
        f"wrote {out}\n  {len(df)} hourly rows, {df[C.TS_COL].min():%Y-%m-%d} -> "
        f"{df[C.TS_COL].max():%Y-%m-%d}\n  carbon intensity: mean {ci.mean():.0f}, "
        f"min {ci.min():.0f}, max {ci.max():.0f} gCO2/kWh\n"
        f"  weather coverage: {df[C.WEATHER_COLS[0]].notna().mean():.0%} of hours"
    )


if __name__ == "__main__":
    main()
