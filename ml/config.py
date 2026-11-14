"""Every tunable for GridGreen lives here. Change values here, never inline."""

from pathlib import Path

# --- Region -----------------------------------------------------------------
# PJM = the grid serving Chicago (ComEd), the mid-Atlantic and parts of the Midwest.
# Electricity Maps zone code for PJM is "US-MIDA-PJM". EIA balancing authority is "PJM".
REGION_NAME = "PJM (Chicago / mid-Atlantic grid)"
ELECTRICITY_MAPS_ZONE = "US-MIDA-PJM"
EIA_BALANCING_AUTHORITY = "PJM"

# --- Paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACTS_DIR = ROOT / "ml" / "artifacts"
RESULTS_DIR = ROOT / "results"

# Put the downloaded Electricity Maps CSV(s) in data/raw/. Any *.csv there is read.
RAW_GLOB = "*.csv"

# --- Canonical column names (what every module downstream expects) ----------
TS_COL = "timestamp"          # tz-aware UTC hourly timestamp
CI_COL = "carbon_intensity"   # gCO2eq per kWh

# Electricity Maps CSV headers -> canonical names. Edit if your download differs.
RAW_COLUMN_MAP = {
    "Datetime (UTC)": TS_COL,
    "Carbon Intensity gCO₂eq/kWh (direct)": CI_COL,
    "Carbon intensity gCO₂eq/kWh (direct)": CI_COL,
    "carbon_intensity_avg": CI_COL,  # older API export name
    "datetime": TS_COL,
}

# --- Split ------------------------------------------------------------------
# Train on everything BEFORE this date, test on everything from it onward.
# Must be far enough back to leave ~3 months of test data. Never shuffle.
SPLIT_DATE = "2024-10-01"

# --- Forecast framing -------------------------------------------------------
HORIZON_HOURS = 24        # predict carbon intensity 24 h ahead of each row
LAG_HOURS = 24            # use the last 24 hours as features
LAST_WEEK_LAG = 168 - HORIZON_HOURS  # value at t-144 == same hour last week of the target
CLEANEST_K = 3            # recommend the k cleanest hours

# --- Model ------------------------------------------------------------------
SEED = 42
MODEL_PARAMS = {
    "max_iter": 300,
    "learning_rate": 0.05,
    "max_depth": 6,
    "random_state": SEED,
}

# --- Synthetic data (for tests and for running the pipeline before the real
# download arrives). NEVER report numbers from synthetic data in the write-up.
SYNTHETIC_DAYS = 400
