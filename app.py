"""GridGreen demo UI.

Run: make app      (or: python -m app)
Opens a local web UI at http://127.0.0.1:7860

Why Gradio and not a separate React frontend: this imports ml/ directly, so there
is no HTTP layer, no CORS, no second deployment and nothing to keep in sync. One
process, works the moment `make train` has produced a model. It also deploys free
to HuggingFace Spaces by pushing this file + requirements.txt.
"""

from __future__ import annotations

from datetime import timedelta

import gradio as gr
import joblib
import numpy as np
import pandas as pd

from ml import config as C
from ml.features import build_features, model_inputs
from ml.recommend import recommend
from ml.train import MODEL_PATH

# Local timezone for display. PJM spans several states; Chicago (ComEd) is our
# reference point, matching config.WEATHER_LAT/LON.
DISPLAY_TZ = "America/Chicago"
HISTORY_HOURS = 192  # 168 needed for ci_lastweek + 24 for the lag window


def _load_recent_history() -> pd.DataFrame:
    """Most recent HISTORY_HOURS of observed carbon intensity.

    Prefers test.csv (the latest data chronologically); falls back to train.csv.
    Raises a clear message if the pipeline hasn't been run yet.
    """
    for name in ("test.csv", "train.csv"):
        path = C.PROCESSED_DIR / name
        if path.exists():
            df = pd.read_csv(path, parse_dates=[C.TS_COL])
            if df[C.TS_COL].dt.tz is None:
                df[C.TS_COL] = df[C.TS_COL].dt.tz_localize("UTC")
            df = df.sort_values(C.TS_COL)
            if len(df) >= HISTORY_HOURS:
                return df.tail(HISTORY_HOURS).reset_index(drop=True)
    raise FileNotFoundError(
        "No processed data found. Run:  make data   (after  python -m ml.fetch)"
    )


def _load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No model at {MODEL_PATH}. Run:  make train")
    return joblib.load(MODEL_PATH)


def _forecast_next_24h(model, hist: pd.DataFrame) -> tuple[pd.DatetimeIndex, np.ndarray]:
    """Predict the 24 hours following the last observation in `hist`.

    Mirrors api/main.py: pad 24 placeholder hours so build_features can form the
    lag window for them, forward-filling carbon intensity (the model only reads
    lags at or before each row's own time, so this does not leak).
    """
    last_ts = hist[C.TS_COL].iloc[-1]
    pad_ts = pd.date_range(last_ts + pd.Timedelta(hours=1), periods=24, freq="h", tz="UTC")
    pad = pd.DataFrame({C.TS_COL: pad_ts, C.CI_COL: np.nan})

    combined = pd.concat([hist[[C.TS_COL, C.CI_COL]], pad], ignore_index=True)
    combined[C.CI_COL] = combined[C.CI_COL].ffill()

    feat = build_features(combined).tail(24)
    preds = model.predict(model_inputs(model, feat))
    return pad_ts, np.asarray(preds, dtype=float)


def run_forecast(load_kwh: float):
    """Gradio callback. Returns (plot_df, headline_md, detail_md)."""
    try:
        model = _load_model()
        hist = _load_recent_history()
    except FileNotFoundError as e:
        empty = pd.DataFrame({"hour": [], "gco2_per_kwh": []})
        return empty, f"### Setup needed\n\n{e}", ""

    pad_ts, preds = _forecast_next_24h(model, hist)
    rec = recommend(list(preds), float(load_kwh))

    local = pad_ts.tz_convert(DISPLAY_TZ)
    plot_df = pd.DataFrame(
        {
            "hour": [t.strftime("%-I %p") for t in local],
            "gco2_per_kwh": np.round(preds, 1),
        }
    )

    best_i = int(np.argmin(preds))
    worst_i = int(np.argmax(preds))
    best_local = local[best_i]
    worst_local = local[worst_i]
    pct = (1 - preds[best_i] / preds[worst_i]) * 100 if preds[worst_i] else 0.0

    headline = (
        f"## Run it at **{best_local.strftime('%-I %p')}** "
        f"({best_local.strftime('%a')})\n\n"
        f"**{preds[best_i]:.0f} gCO₂/kWh** — about **{pct:.0f}% cleaner** "
        f"than the dirtiest hour ({worst_local.strftime('%-I %p')}, "
        f"{preds[worst_i]:.0f} gCO₂/kWh).\n\n"
        f"Shifting a **{load_kwh:.1f} kWh** load from the worst hour to the best "
        f"saves **{rec['co2_saved_kg']:.2f} kg CO₂**."
    )

    top3 = [
        f"- {local[h].strftime('%-I %p')} — {preds[h]:.0f} gCO₂/kWh"
        for h in rec["cleanest_hours_utc"]
    ]
    detail = (
        f"**Three cleanest hours**\n\n" + "\n".join(top3) + "\n\n"
        f"**Region:** {C.REGION_NAME}\n\n"
        f"**Forecast window:** {local[0].strftime('%a %-I %p')} → "
        f"{local[-1].strftime('%a %-I %p')} ({DISPLAY_TZ})\n\n"
        f"**Based on** observed carbon intensity through "
        f"{hist[C.TS_COL].iloc[-1].tz_convert(DISPLAY_TZ).strftime('%a %-I %p')}.\n\n"
        f"*Prototype — not official grid data.*"
    )
    return plot_df, headline, detail


with gr.Blocks(title="GridGreen", theme=gr.themes.Soft(primary_hue="emerald")) as demo:
    gr.Markdown(
        "# GridGreen\n"
        "### When should you run your laundry, dishwasher or EV charger?\n"
        f"Next-24-hour carbon intensity forecast for **{C.REGION_NAME}**."
    )

    with gr.Row():
        with gr.Column(scale=1):
            load = gr.Slider(
                0.5, 60, value=7.0, step=0.5,
                label="Load to shift (kWh)",
                info="Laundry ≈ 2 kWh · Dishwasher ≈ 1.5 kWh · EV charge ≈ 7–60 kWh",
            )
            go = gr.Button("Find the cleanest hour", variant="primary")
            detail_md = gr.Markdown()
        with gr.Column(scale=2):
            headline_md = gr.Markdown()
            plot = gr.LinePlot(
                x="hour",
                y="gco2_per_kwh",
                title="Forecast carbon intensity, next 24 hours",
                x_title="Hour (local)",
                y_title="gCO₂ per kWh",
                height=320,
                overlay_point=True,
            )

    go.click(run_forecast, inputs=[load], outputs=[plot, headline_md, detail_md])
    demo.load(run_forecast, inputs=[load], outputs=[plot, headline_md, detail_md])


if __name__ == "__main__":
    demo.launch()
