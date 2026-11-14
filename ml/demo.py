"""Gradio fallback demo. Run: make demo  -> opens http://127.0.0.1:7860

Shows: pick a test day -> true vs persistence vs model curves, cleanest hours, CO2 saved.
"""

from __future__ import annotations

import gradio as gr
import pandas as pd

from ml import config as C
from ml.features import TARGET_COL, TARGET_TS_COL
from ml.recommend import recommend

PRED = pd.read_csv(C.RESULTS_DIR / "test_predictions.csv", parse_dates=[TARGET_TS_COL])
PRED["day"] = PRED[TARGET_TS_COL].dt.date.astype(str)
DAYS = sorted(d for d, g in PRED.groupby("day") if len(g) == 24)


def show(day: str, load_kwh: float):
    g = PRED[PRED["day"] == day].sort_values(TARGET_TS_COL)
    rec = recommend(g["pred_model"].tolist(), load_kwh)
    true_rec = recommend(g[TARGET_COL].tolist(), load_kwh)
    plot = pd.DataFrame({
        "hour (UTC)": g[TARGET_TS_COL].dt.hour,
        "actual": g[TARGET_COL].values,
        "persistence": g["pred_persistence"].values,
        "model": g["pred_model"].values,
    })
    text = (
        f"**Model says charge at hours {rec['cleanest_hours_utc']} UTC** → saves "
        f"{rec['co2_saved_kg']} kg CO₂ vs the dirtiest hour.\n\n"
        f"Truth: cleanest hours were {true_rec['cleanest_hours_utc']} "
        f"({len(set(rec['cleanest_hours_utc']) & set(true_rec['cleanest_hours_utc']))}/3 overlap)."
    )
    return plot, text


with gr.Blocks(title="GridGreen") as app:
    gr.Markdown(f"# GridGreen — next-day carbon intensity, {C.REGION_NAME}")
    day = gr.Dropdown(DAYS, value=DAYS[-1], label="Test day (never seen in training)")
    load = gr.Number(value=7.0, label="Flexible load to shift (kWh), e.g. one EV charge")
    plot = gr.LinePlot(x="hour (UTC)", y="actual", label="gCO₂/kWh")
    out = gr.Markdown()
    btn = gr.Button("Forecast")
    btn.click(show, [day, load], [plot, out])

if __name__ == "__main__":
    app.launch()
