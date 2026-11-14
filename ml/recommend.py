"""Turn a 24-hour forecast into the decision a user makes: when to run a flexible load."""

from __future__ import annotations

import numpy as np

from ml import config as C


def recommend(forecast: list[float], load_kwh: float, k: int = C.CLEANEST_K) -> dict:
    """Given 24 hourly gCO2/kWh forecasts (index 0 = hour 0 of tomorrow, UTC) and a load
    in kWh, return the k cleanest hours and the CO2 saved by moving the load from the
    single dirtiest hour to the single cleanest hour."""
    f = np.asarray(forecast, dtype=float)
    if f.shape != (24,):
        raise ValueError(f"forecast must have 24 values, got {f.shape}")
    if load_kwh < 0:
        raise ValueError("load_kwh must be >= 0")
    order = np.argsort(f)
    cleanest = [int(h) for h in order[:k]]
    dirtiest = int(order[-1])
    saved_g = (f[dirtiest] - f[cleanest[0]]) * load_kwh
    return {
        "cleanest_hours_utc": cleanest,
        "dirtiest_hour_utc": dirtiest,
        "co2_saved_kg": round(float(saved_g) / 1000, 3),
        "forecast_gco2_per_kwh": [round(float(x), 1) for x in f],
    }
