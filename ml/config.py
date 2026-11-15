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

# `make fetch` writes one tidy CSV here (data/raw/gridgreen_<BA>.csv). Any *.csv directly
# in data/raw/ is read by `make data`; the big EIA downloads are cached in a sub-folder.
RAW_GLOB = "*.csv"
EIA_CACHE_DIR = RAW_DIR / "eia_cache"

# --- Real data sources (ml/fetch.py) -----------------------------------------
# 1) EIA-930 Hourly Electric Grid Monitor, six-month "balance" files. Public, no API key.
#    One file per half-year, all balancing authorities; we keep only ours.
EIA_BALANCE_URL = (
    "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"
    "EIA930_BALANCE_{year}_{half}.csv"
)
FETCH_START_YEAR = 2024   # first year to download (2 halves per year)

# Direct (smokestack) CO2 per kWh generated, in grams. EIA national averages for 2023:
# coal 2.31 lb/kWh, natural gas 0.96 lb/kWh, petroleum 2.46 lb/kWh (x 453.6 g/lb).
# Source: EIA FAQ "How much carbon dioxide is produced per kWh of U.S. electricity
# generation?" (2023 factors) https://www.eia.gov/tools/faqs/faq.php?id=74
# Nuclear, hydro, wind, solar, geothermal and storage are counted as 0 (direct emissions).
# "Other" is mostly waste/biomass; we treat it like gas. This is an approximation and
# must be stated in the write-up.
EMISSION_FACTORS_G_PER_KWH = {"coal": 1048.0, "gas": 435.0, "oil": 1116.0, "other": 435.0}

# 2) Open-Meteo historical weather API. Public, no key, CC BY 4.0.
#    One point stands in for the whole region (a limitation: PJM spans 13 states).
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_LAT, WEATHER_LON = 41.88, -87.63          # Chicago (ComEd zone of PJM)
WEATHER_VARS = {                                    # Open-Meteo name -> our column
    "temperature_2m": "temp_c",
    "wind_speed_100m": "wind_ms",
    "shortwave_radiation": "solar_wm2",
    "cloud_cover": "cloud_pct",
}

# Extra columns (besides carbon intensity) that become model features, using the value
# at time t only (never the future). Missing ones are left empty; the model copes.
MIX_COLS = ["demand_mw", "coal_share", "gas_share", "nuclear_share", "wind_share", "solar_share"]
WEATHER_COLS = list(WEATHER_VARS.values())
EXTRA_COLS = MIX_COLS + WEATHER_COLS

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
# Real data runs Jan 2024 -> yesterday, so Aug 1 2026 leaves ~3.5 months of test.
SPLIT_DATE = "2026-08-01"
VALIDATION_START = "2026-05-01"
LOCAL_TIMEZONE = "America/Chicago"

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
