"""GridGreen historical replay dashboard.

Run ``make app`` and open http://127.0.0.1:7860. The interface replays the
latest processed, historical 24-hour window; it is not a live forecast.
"""

from __future__ import annotations

import html
import json
from functools import lru_cache

import gradio as gr
import joblib
import numpy as np
import pandas as pd

from ml import config as C
from ml.baseline import persistence
from ml.features import build_features, model_inputs
from ml.recommend import recommend
from ml.train import MODEL_PATH

DISPLAY_TZ = "America/Chicago"
MODEL_LABEL = "GridGreen model"
PERSIST_LABEL = "Persistence · today repeated"
HISTORY_HOURS = 192
CSS_PATH = C.ROOT / "assets" / "gridgreen.css"

# IBM Plex is the project's interface typeface. The system fallbacks in the CSS
# keep the dashboard legible if a demo machine is offline.
FONT_HEAD = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
"""


def _load_recent_history() -> pd.DataFrame:
    """Return the most recent observed history from processed data."""
    for name in ("test.csv", "train.csv"):
        path = C.PROCESSED_DIR / name
        if not path.exists():
            continue
        frame = pd.read_csv(path, parse_dates=[C.TS_COL]).sort_values(C.TS_COL)
        if frame[C.TS_COL].dt.tz is None:
            frame[C.TS_COL] = frame[C.TS_COL].dt.tz_localize("UTC")
        if len(frame) >= HISTORY_HOURS:
            return frame.tail(HISTORY_HOURS).reset_index(drop=True)
    raise FileNotFoundError(
        "Processed history is unavailable. Run `make data`, then reload this page."
    )


@lru_cache(maxsize=1)
def _load_model():
    """Load the trained model once, or explain how to create it."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"The trained model is unavailable at {MODEL_PATH}. Run `make train`."
        )
    return joblib.load(MODEL_PATH)


def _forecast_next_24h(
    model, history: pd.DataFrame
) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray]:
    """Return target times, model predictions, and persistence predictions."""
    last_ts = history[C.TS_COL].iloc[-1]
    target_ts = pd.date_range(
        last_ts + pd.Timedelta(hours=1), periods=24, freq="h", tz="UTC"
    )
    placeholder = pd.DataFrame({C.TS_COL: target_ts, C.CI_COL: np.nan})

    # build_features creates a target 24 hours after each input row. Filling the
    # placeholder target values lets it retain the final 24 observed input rows;
    # the model still reads only those rows and their earlier lags.
    combined = pd.concat([history, placeholder], ignore_index=True)
    combined[C.CI_COL] = combined[C.CI_COL].ffill()
    features = build_features(combined).tail(24)
    predicted = model.predict(model_inputs(model, features))
    baseline = persistence(features).to_numpy(dtype=float)
    return target_ts, np.asarray(predicted, dtype=float), baseline


def _empty_plot() -> pd.DataFrame:
    """Return a correctly shaped empty plot frame for setup errors."""
    return pd.DataFrame(columns=["hour", "gco2_per_kwh", "forecast"])


def _error_panel(message: str) -> str:
    """Render a visible setup message without substituting fake values."""
    return f"""
    <section class="hero-panel setup-panel" role="alert">
      <div class="hero-kicker"><span class="status-dot status-dot--amber"></span>Setup required</div>
      <h1>Forecast replay unavailable</h1>
      <p>{html.escape(message)}</p>
      <p class="microcopy">No forecast values have been substituted.</p>
    </section>
    """


def _window_label(local_times: pd.DatetimeIndex) -> str:
    """Format the exact historical replay window in local time."""
    start = local_times[0]
    end = local_times[-1]
    if start.date() == end.date():
        return f"{start.strftime('%b %-d, %Y')} · {start.strftime('%-I %p')}–{end.strftime('%-I %p')} CT"
    return (
        f"{start.strftime('%b %-d, %-I %p')}–"
        f"{end.strftime('%b %-d, %-I %p %Y')} CT"
    )


def _hero_html(
    local_times: pd.DatetimeIndex,
    predicted: np.ndarray,
    recommendation: dict,
    load_kwh: float,
) -> str:
    """Render the decision-first hero using generated forecast values."""
    cleanest = recommendation["cleanest_hours_utc"]
    best = cleanest[0]
    worst = recommendation["dirtiest_hour_utc"]
    difference = predicted[worst] - predicted[best]
    cards = "".join(
        f"""
        <li>
          <span class="rank">0{rank}</span>
          <span class="recommended-time">{local_times[index].strftime('%-I %p')}</span>
          <span class="recommended-day">{local_times[index].strftime('%a')}</span>
          <span class="recommended-intensity">{predicted[index]:.0f} <small>gCO₂/kWh</small></span>
        </li>
        """
        for rank, index in enumerate(cleanest, start=1)
    )
    return f"""
    <section class="hero-panel" aria-live="polite">
      <div class="hero-kicker"><span class="status-dot"></span>Historical replay · {_window_label(local_times)}</div>
      <div class="hero-grid">
        <div class="hero-primary">
          <p class="overline">Cleanest predicted hour</p>
          <h1>{local_times[best].strftime('%-I %p')} <span>{local_times[best].strftime('%A')}</span></h1>
          <div class="hero-measurement"><strong>{predicted[best]:.0f}</strong><span>gCO₂ / kWh</span></div>
          <p class="hero-context">Lowest modeled average intensity in this historical 24-hour forecast window.</p>
        </div>
        <div class="hero-recommendations">
          <div class="section-label"><span>Recommended sequence</span><span>Lowest first</span></div>
          <ol>{cards}</ol>
        </div>
      </div>
      <div class="hero-footer">
        <span>Load scenario <b>{load_kwh:.1f} kWh</b></span>
        <span>Modeled average-intensity difference <b>{difference:.0f} gCO₂/kWh</b></span>
        <span>Illustrative load difference <b>{recommendation['co2_saved_kg']:.2f} kg CO₂</b></span>
      </div>
    </section>
    """


def _plot_frame(
    local_times: pd.DatetimeIndex, predicted: np.ndarray, baseline: np.ndarray
) -> pd.DataFrame:
    """Return long-form chart data with fixed Chicago-time labels."""
    labels = [time.strftime("%-I %p") for time in local_times]
    day_labels = [time.strftime("%a %-I %p") for time in local_times]
    frames = []
    for values, name in ((predicted, MODEL_LABEL), (baseline, PERSIST_LABEL)):
        frames.append(
            pd.DataFrame(
                {
                    "hour": labels,
                    "local_time": day_labels,
                    "gco2_per_kwh": np.round(values, 1),
                    "forecast": name,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _strip_html(
    local_times: pd.DatetimeIndex, predicted: np.ndarray, cleanest: list[int]
) -> str:
    """Render all 24 modeled intensities and mark each recommended hour."""
    spread = float(np.ptp(predicted))
    recommendation_ranks = {index: rank for rank, index in enumerate(cleanest, 1)}
    cells = []
    for index, (time, value) in enumerate(zip(local_times, predicted, strict=True)):
        level = int(round(((value - predicted.min()) / spread) * 4)) if spread else 0
        rank = recommendation_ranks.get(index)
        selected_class = " strip-cell--selected" if rank else ""
        badge = f'<span class="strip-rank">Clean 0{rank}</span>' if rank else ""
        label = (
            f"{time.strftime('%A %-I %p')}, {value:.0f} grams CO2 per kilowatt-hour"
            + (f", clean recommendation {rank}" if rank else "")
        )
        cells.append(
            f"""
            <div class="strip-cell intensity-{level}{selected_class}" role="listitem" aria-label="{label}">
              {badge}
              <span class="strip-time">{time.strftime('%-I%p').lower()}</span>
              <strong>{value:.0f}</strong>
              <small>g/kWh</small>
            </div>
            """
        )
    return f"""
    <section class="strip-section" aria-live="polite">
      <div class="section-heading compact-heading">
        <div><p class="overline">24-hour intensity scan</p><h2>Cleaner to dirtier periods</h2></div>
        <div class="strip-legend" aria-label="Color legend"><span class="legend-clean"></span>Cleaner<span class="legend-dirty"></span>Dirtier</div>
      </div>
      <div class="intensity-strip" role="list">{''.join(cells)}</div>
      <p class="scroll-hint">Scroll horizontally to inspect all 24 hours on a small screen.</p>
    </section>
    """


def _metrics_html() -> str:
    """Render held-out results directly from results/metrics.json."""
    path = C.RESULTS_DIR / "metrics.json"
    if not path.exists():
        return _error_panel("Held-out metrics are unavailable. Run `make eval`.")
    try:
        metrics = json.loads(path.read_text())
        model = metrics["model"]
        baseline = metrics["persistence"]
        meta = metrics["_meta"]
        reduction = (baseline["mae"] - model["mae"]) / baseline["mae"] * 100
        overlap_gap = (model["cleanest_3_overlap"] - baseline["cleanest_3_overlap"]) * 100
    except (KeyError, TypeError, ValueError, ZeroDivisionError, json.JSONDecodeError) as error:
        return _error_panel(f"Held-out metrics could not be read: {error}")

    if overlap_gap >= 0:
        overlap_note = f"Model leads by {overlap_gap:.1f} percentage points."
        results_heading = "Closer values and stronger clean-hour picks."
    else:
        overlap_note = f"Persistence leads by {abs(overlap_gap):.1f} percentage points."
        results_heading = "Closer values. No clean-hour win."
    if reduction >= 0:
        mae_note = f"The model reduces MAE by <b>{reduction:.1f}%</b> on the same held-out period."
    else:
        mae_note = f"The model increases MAE by <b>{abs(reduction):.1f}%</b> on the same held-out period."
    return f"""
    <section class="results-panel">
      <div class="section-heading">
        <div><p class="overline">Held-out evaluation</p><h2>{results_heading}</h2></div>
        <p>{html.escape(str(meta.get('test_period', 'Period unavailable')))} · {html.escape(str(meta.get('test_rows', '?')))} hourly forecasts</p>
      </div>
      <div class="metric-grid">
        <article>
          <div class="metric-title"><span>Mean absolute error</span><span>Lower is better</span></div>
          <div class="metric-comparison"><div><small>Model</small><strong>{model['mae']:.2f}</strong></div><div><small>Persistence</small><strong>{baseline['mae']:.2f}</strong></div></div>
          <p>{mae_note}</p>
        </article>
        <article>
          <div class="metric-title"><span>Cleanest-three overlap</span><span>Higher is better</span></div>
          <div class="metric-comparison"><div><small>Model</small><strong>{model['cleanest_3_overlap']:.3f}</strong></div><div><small>Persistence</small><strong>{baseline['cleanest_3_overlap']:.3f}</strong></div></div>
          <p>{overlap_note} The model does not beat the simple baseline on this decision metric.</p>
        </article>
      </div>
    </section>
    """


def run_forecast(load_kwh: float):
    """Update the replay chart and decision panels for a load scenario."""
    try:
        load = float(load_kwh)
        if not np.isfinite(load) or not 0.5 <= load <= 60:
            raise ValueError("Load must be between 0.5 and 60 kWh.")
        model = _load_model()
        history = _load_recent_history()
        target_ts, predicted, baseline = _forecast_next_24h(model, history)
    except (FileNotFoundError, ValueError) as error:
        message = str(error)
        return _error_panel(message), _empty_plot(), _error_panel(message)

    local_times = target_ts.tz_convert(DISPLAY_TZ)
    recommendation = recommend(list(predicted), load)
    return (
        _hero_html(local_times, predicted, recommendation, load),
        _plot_frame(local_times, predicted, baseline),
        _strip_html(local_times, predicted, recommendation["cleanest_hours_utc"]),
    )


THEME = gr.themes.Base(
    primary_hue="teal",
    neutral_hue="slate",
)

# Build the initial replay before the server starts so a screen recording never
# catches an empty hero or chart while a browser-side load event is queued.
INITIAL_HERO, INITIAL_PLOT, INITIAL_STRIP = run_forecast(7.0)

with gr.Blocks(title="GridGreen · Historical replay") as demo:
    with gr.Column(elem_id="gridgreen-app"):
        gr.HTML(
            """
            <header class="topbar">
              <a class="wordmark" href="#gridgreen-app" aria-label="GridGreen dashboard home"><span>GRID</span>GREEN</a>
              <nav aria-label="Replay context"><span>PJM</span><span>Historical replay</span></nav>
              <div class="system-state"><span class="status-dot"></span>Model ready</div>
            </header>
            """
        )

        hero = gr.HTML(value=INITIAL_HERO, elem_id="forecast-hero")

        with gr.Group(elem_classes="load-panel"):
            with gr.Row(elem_classes="load-layout"):
                gr.HTML(
                    """
                    <div class="load-intro">
                      <p class="overline">Scenario control</p>
                      <h2>What are you scheduling?</h2>
                      <p>Choose an illustrative preset or set the energy use directly. This changes only the load difference—not the forecast.</p>
                    </div>
                    """
                )
                with gr.Column(elem_classes="load-controls"):
                    with gr.Row(elem_classes="preset-row"):
                        laundry = gr.Button(
                            "Laundry · 2 kWh*", elem_classes="preset-button"
                        )
                        dishwasher = gr.Button(
                            "Dishwasher · 1.5 kWh*", elem_classes="preset-button"
                        )
                        ev_charge = gr.Button(
                            "EV charging · 40 kWh*", elem_classes="preset-button"
                        )
                    load = gr.Slider(
                        minimum=0.5,
                        maximum=60,
                        value=7.0,
                        step=0.5,
                        label="Flexible load (kWh)",
                        info="*Preset energy values are illustrative. Adjust for the actual appliance or vehicle.",
                        elem_id="load-slider",
                    )

        gr.HTML(
            """
            <div class="section-heading chart-heading">
              <div><p class="overline">Forecast trace</p><h2>Model vs. persistence</h2></div>
              <p>Persistence repeats the observed intensity from 24 hours earlier. Hover or focus the chart for exact values.</p>
            </div>
            """
        )
        plot = gr.LinePlot(
            value=INITIAL_PLOT,
            x="hour",
            y="gco2_per_kwh",
            color="forecast",
            x_title="Historical target hour · Central Time",
            y_title="Carbon intensity · gCO₂/kWh",
            color_title="Forecast",
            height=430,
            color_map={MODEL_LABEL: "#4EC9B0", PERSIST_LABEL: "#AAB5C4"},
            tooltip=["local_time", "forecast", "gco2_per_kwh"],
            sort=[
                "12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM",
                "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM",
                "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM",
                "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM",
            ],
            buttons=["fullscreen", "export"],
            elem_id="forecast-chart",
        )

        strip = gr.HTML(value=INITIAL_STRIP, elem_id="intensity-strip-output")
        gr.HTML(_metrics_html(), elem_id="heldout-results")
        gr.HTML(
            """
            <section class="method-panel">
              <div class="section-heading"><div><p class="overline">How to read this system</p><h2>A forecast for a decision—not a guarantee.</h2></div></div>
              <div class="method-grid">
                <article><span>01 · What it does</span><h3>Learns tomorrow's shape</h3><p>A gradient-boosted model uses the previous 24 hours, the same hour last week, calendar signals, and fuel-mix and Chicago weather observed at forecast time.</p></article>
                <article><span>02 · Where it fails</span><h3>Sudden level shifts</h3><p>The worst held-out days are dominated by whole-day offsets. Changes in wind and demand after the forecast origin are invisible without archived weather forecasts.</p></article>
                <article><span>03 · Boundaries</span><h3>Average direct emissions</h3><p>This historical replay is not a live forecast. National-average direct-emission factors are not marginal avoided emissions, and one Chicago weather point cannot represent all of PJM.</p></article>
              </div>
              <div class="disclaimer"><strong>Scientific note</strong><p>The load result is a modeled average-intensity difference between the dirtiest and cleanest predicted hour. It is illustrative—not guaranteed CO₂ savings. EIA observations may also be published too late for a strict operational 24-hour-ahead forecast.</p></div>
            </section>
            <footer class="dashboard-footer"><span>GRIDGREEN · VERITAS AI CLIMATE TRACK</span><span>Data: EIA-930 + Open-Meteo · Model: scikit-learn</span></footer>
            """,
            elem_id="methodology",
        )

    forecast_outputs = [hero, plot, strip]
    load.change(
        run_forecast,
        inputs=[load],
        outputs=forecast_outputs,
        show_progress="hidden",
        trigger_mode="always_last",
        api_visibility="private",
    )
    for button, value in ((laundry, 2.0), (dishwasher, 1.5), (ev_charge, 40.0)):
        button.click(
            lambda preset=value: preset,
            outputs=[load],
            show_progress="hidden",
            api_visibility="private",
        )


if __name__ == "__main__":
    demo.launch(
        theme=THEME,
        css_paths=CSS_PATH,
        head=FONT_HEAD,
        footer_links=[],
    )
