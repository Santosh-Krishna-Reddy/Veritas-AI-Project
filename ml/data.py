"""Load raw carbon-intensity data, clean it, split ONCE by date, save to data/processed/.

Run:  python -m ml.data              (reads data/raw/*.csv)
      python -m ml.data --synthetic  (generates fake data so the pipeline runs end to end;
                                      results from it are NOT real and must not be reported)
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from ml import config as C


def load_raw(raw_dir=C.RAW_DIR) -> pd.DataFrame:
    """Read every CSV in data/raw/, rename columns to canonical names, return one frame."""
    files = sorted(raw_dir.glob(C.RAW_GLOB))
    if not files:
        sys.exit(
            f"No CSV files in {raw_dir}. Run `make fetch` to download real EIA + weather "
            f"data for {C.EIA_BALANCING_AUTHORITY}, or run with --synthetic."
        )
    frames = [pd.read_csv(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={k: v for k, v in C.RAW_COLUMN_MAP.items() if k in df.columns})
    missing = {C.TS_COL, C.CI_COL} - set(df.columns)
    if missing:
        sys.exit(
            f"Raw CSV is missing {missing}. Columns found: {list(df.columns)}. "
            f"Update RAW_COLUMN_MAP in ml/config.py."
        )
    extras = [c for c in C.EXTRA_COLS if c in df.columns]
    return df[[C.TS_COL, C.CI_COL] + extras]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Parse timestamps, sort, drop duplicates, fill short gaps, validate. Returns a new frame."""
    out = df.copy()
    out[C.TS_COL] = pd.to_datetime(out[C.TS_COL], utc=True)
    out = out.sort_values(C.TS_COL).drop_duplicates(C.TS_COL)
    out[C.CI_COL] = pd.to_numeric(out[C.CI_COL], errors="coerce")

    # Re-index to a complete hourly range so lags line up, then fill gaps <= 3 h.
    full = pd.date_range(out[C.TS_COL].min(), out[C.TS_COL].max(), freq="h", tz="UTC")
    out = out.set_index(C.TS_COL).reindex(full)
    n_gap = int(out[C.CI_COL].isna().sum())
    out[C.CI_COL] = out[C.CI_COL].interpolate(limit=3, limit_direction="both")
    # Extra columns (fuel mix, weather): carry the last known value forward up to 3 h.
    # Longer gaps stay empty -- we only drop rows where carbon intensity itself is missing.
    extras = [c for c in C.EXTRA_COLS if c in out.columns]
    out[extras] = out[extras].apply(pd.to_numeric, errors="coerce").ffill(limit=3)
    out = out.dropna(subset=[C.CI_COL]).rename_axis(C.TS_COL).reset_index()

    # Validate at the boundary: fail fast on garbage.
    assert (out[C.CI_COL] >= 0).all(), "negative carbon intensity found"
    assert out[C.CI_COL].max() < 2000, "carbon intensity > 2000 g/kWh looks wrong"
    assert len(out) > 24 * 60, f"only {len(out)} hourly rows; need at least 60 days"
    print(f"clean: {len(out)} hourly rows, {n_gap} gap hours interpolated/dropped")
    return out


def split_by_date(df: pd.DataFrame, split_date: str = C.SPLIT_DATE):
    """Train = before split_date, test = from split_date on. Never shuffles."""
    cut = pd.Timestamp(split_date, tz="UTC")
    train = df[df[C.TS_COL] < cut].reset_index(drop=True)
    test = df[df[C.TS_COL] >= cut].reset_index(drop=True)
    if len(train) < 24 * 30 or len(test) < 24 * 30:
        sys.exit(
            f"Split at {split_date} gives train={len(train)} test={len(test)} hourly rows. "
            f"Each needs >= 30 days. Move SPLIT_DATE in ml/config.py."
        )
    assert train[C.TS_COL].max() < test[C.TS_COL].min(), "train/test overlap"
    return train, test


def make_synthetic(days: int = C.SYNTHETIC_DAYS, seed: int = C.SEED) -> pd.DataFrame:
    """Fake but realistic hourly carbon intensity: daily shape + weekly + seasonal + noise."""
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2024-01-01", periods=days * 24, freq="h", tz="UTC")
    hour = ts.hour.values
    doy = ts.dayofyear.values
    weekday = ts.weekday.values
    daily = 60 * np.cos((hour - 4) / 24 * 2 * np.pi)          # cleanest mid-day (solar)
    weekly = np.where(weekday >= 5, -25, 0)                      # weekends are cleaner
    seasonal = 40 * np.cos((doy - 200) / 365 * 2 * np.pi)       # dirtier in winter
    noise = rng.normal(0, 25, len(ts)) + np.repeat(rng.normal(0, 30, days), 24)
    ci = 420 + daily + weekly + seasonal + noise
    return pd.DataFrame({C.TS_COL: ts, C.CI_COL: ci.clip(50, 900)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true", help="generate fake data")
    args = parser.parse_args()

    C.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw = make_synthetic() if args.synthetic else load_raw()
    df = clean(raw)
    train, test = split_by_date(df)
    train.to_csv(C.PROCESSED_DIR / "train.csv", index=False)
    test.to_csv(C.PROCESSED_DIR / "test.csv", index=False)
    (C.PROCESSED_DIR / "SOURCE.txt").write_text(
        "SYNTHETIC - not real data, do not report\n" if args.synthetic else "real\n"
    )
    print(
        f"train: {len(train)} rows {train[C.TS_COL].min():%Y-%m-%d} -> "
        f"{train[C.TS_COL].max():%Y-%m-%d}\n"
        f"test:  {len(test)} rows {test[C.TS_COL].min():%Y-%m-%d} -> "
        f"{test[C.TS_COL].max():%Y-%m-%d}"
    )


if __name__ == "__main__":
    main()
