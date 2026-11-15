"""Six figures for the README and the demo video, plus one-sentence captions.

Every number in a title or caption is read from results/decision_metrics.json (written by
`python -m ml.decision`, run that first). Plots are 1600x900 px
with large fonts so they stay readable in a 1080p video.

Colours: Okabe-Ito palette (colour-blind safe). Truth is always near-black, persistence
always grey, the model always blue; other forecasts get the remaining Okabe-Ito colours.

Writes: results/figures/0*.png and results/figures/captions.md
Run: python -m ml.figures
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ml import config as C
from ml.decision import LOCAL_TZ, OUT_PATH, PRIMARY, load_predictions, pred_columns

FIG_DIR = C.RESULTS_DIR / "figures"
SIZE, DPI = (16, 9), 100  # 16 x 9 inches at 100 dpi = 1600 x 900 px
FIXED = {"truth": "#1a1a1a", "persistence": "#8c8c8c", "model": "#0072B2"}
OTHERS = ["#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442"]
SOURCE = ("Source: EIA-930 Hourly Electric Grid Monitor (PJM), carbon intensity computed by "
          "GridGreen from EIA emission factors; {period}.")
plt.rcParams.update({"font.size": 18, "axes.titlesize": 22, "axes.labelsize": 18,
                     "axes.spines.top": False, "axes.spines.right": False})


def colour(name: str, names: list[str]) -> str:
    """Same colour for the same series in every figure."""
    if name in FIXED:
        return FIXED[name]
    rest = [n for n in names if n not in FIXED]
    return OTHERS[rest.index(name) % len(OTHERS)]


def finish(fig: plt.Figure, name: str, period: str) -> None:
    """Add the source line at the bottom and save at exactly 1600x900."""
    fig.text(0.01, 0.01, SOURCE.format(period=period), fontsize=12, color="#555555")
    fig.savefig(FIG_DIR / name, dpi=DPI)
    plt.close(fig)


def fig_week(preds: pd.DataFrame, d: dict, period: str) -> str:
    """01: the 7 days centred on the model's worst test day: truth, model, persistence."""
    w = d["worst_model_day"]
    mid = pd.Timestamp(w["day"], tz="UTC")
    win = preds[(preds["target_timestamp"] >= mid - pd.Timedelta(days=3)) &
                (preds["target_timestamp"] < mid + pd.Timedelta(days=4))]
    x = win["target_timestamp"].dt.tz_convert(LOCAL_TZ).dt.tz_localize(None)
    fig, ax = plt.subplots(figsize=SIZE)
    ax.axvspan(mid.tz_convert(LOCAL_TZ).tz_localize(None),
               (mid + pd.Timedelta(days=1)).tz_convert(LOCAL_TZ).tz_localize(None),
               color="#0072B2", alpha=0.08, label=f"worst day ({w['day']} UTC)")
    for name, col, lw in [("truth", "target", 3.5), ("persistence", "pred_persistence", 2.5),
                          (w["forecast"], f"pred_{w['forecast']}", 2.5)]:
        ax.plot(x, win[col], color=colour(name, list(FIXED)), lw=lw, label=name)
    ax.set_title(f"Worst test day {w['day']}: the model missed by {w['mae']:.0f} g/kWh on average "
                 f"(persistence {w['persistence_mae']:.0f})", loc="left")
    ax.set_ylabel("Carbon intensity (gCO₂/kWh)")
    ax.set_xlabel("Date (Chicago time)")
    ax.legend(frameon=False, ncol=4, loc="upper left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    finish(fig, "01_week.png", f"test period {period}")
    return (f"In the week around {w['day']}, the model's worst test day, it missed by "
            f"{w['mae']:.1f} gCO₂/kWh on average, against {w['persistence_mae']:.1f} for persistence.")


def fig_shape(d: dict, period: str) -> str:
    """02: heatmap of mean intensity by Chicago hour of day x month, all data."""
    s = d["daily_shape_all_data"]
    months = [pd.Timestamp(2024, m, 1).strftime("%b") for m in s["months"]]
    fig, ax = plt.subplots(figsize=SIZE)
    im = ax.imshow(np.array(s["grid"]), aspect="auto", cmap="cividis_r")
    ax.set_xticks(range(0, 24, 2), [f"{h}:00" for h in s["hours"][::2]])
    ax.set_yticks(range(len(months)), months)
    ax.set_xlabel("Hour of day (Chicago time)")
    fig.colorbar(im, ax=ax, label="Mean carbon intensity (gCO₂/kWh)")
    lo, hi = min(s["cleanest_hour_per_month"]), max(s["cleanest_hour_per_month"])
    ax.set_title(f"In every month the cleanest hour falls between {lo}:00 and {hi}:00;\n"
                 f"evenings around {s['dirtiest_hour']}:00 are dirtiest (Chicago time)", loc="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    finish(fig, "02_shape.png", f"all data {s['first']} to {s['last']}, train + test")
    return (f"Averaged over all data ({s['first']} to {s['last']}), PJM is cleanest around "
            f"{s['cleanest_hour']}:00 and dirtiest around {s['dirtiest_hour']}:00 Chicago time, "
            f"with an average daily swing of {s['mean_daily_swing']:.1f} gCO₂/kWh between the "
            f"cleanest and dirtiest hour of a month.")


def fig_scoreboard(d: dict, period: str) -> str:
    """03: MAE and share of possible saving captured, for every forecast."""
    main = d["sensitivity"][f"{PRIMARY[0]}|k={PRIMARY[1]}"]
    names = d["forecasts"]
    cols = [colour(n, names) for n in names]
    mae = [d["mae_all_test_rows"][n] for n in names]
    cap = [100 * main[n]["captured_pooled"] for n in names]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=SIZE)
    for ax, vals, label, fmt in [(a1, mae, "MAE (gCO₂/kWh), lower is better", "{:.1f}"),
                                 (a2, cap, "Possible saving captured (%), higher is better", "{:.0f}%")]:
        bars = ax.barh(names, vals, color=cols)
        ax.bar_label(bars, [fmt.format(v) for v in vals], padding=6)
        ax.set_xlabel(label)
        ax.invert_yaxis()
    a2.set_yticks([])
    a2.set_xlim(0, 100)
    best_mae, best_cap = names[int(np.argmin(mae))], names[int(np.argmax(cap))]
    boot = main["regret_minus_persistence"].get("model", {})
    ci = boot.get("ci95", [float("nan")] * 2)
    edge = "within noise" if ci[0] <= 0 <= ci[1] else "outside noise"  # does the 95% CI hit 0?
    fig.suptitle(f"Lowest error: {best_mae}. Most saving captured: {best_cap}.\n"
                 f"Model vs persistence on CO₂ regret: {edge} (95% CI {ci[0]:+.1f} to {ci[1]:+.1f} g/kWh)",
                 x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    finish(fig, "03_scoreboard.png", f"test period {period}")
    m = d["mae_all_test_rows"]
    return (f"MAE: model {m['model']:.2f} vs persistence {m['persistence']:.2f} gCO₂/kWh; "
            f"share of possible saving captured: model {100 * main['model']['captured_pooled']:.1f}% "
            f"vs persistence {100 * main['persistence']['captured_pooled']:.1f}%; model minus "
            f"persistence regret {boot.get('mean_diff', float('nan')):+.2f} g/kWh "
            f"(95% bootstrap CI {ci[0]:+.2f} to {ci[1]:+.2f}, {edge}).")


def fig_when_wrong(d: dict, period: str) -> str:
    """04: MAE by Chicago hour of day, weekday vs weekend, model and persistence."""
    mae = d["breakdowns"]["hour_chicago|day_type"]["mae"]
    fig, ax = plt.subplots(figsize=SIZE)
    peak = {}
    for name in ["model", "persistence"]:
        for kind, style in [("weekday", "-"), ("weekend", "--")]:
            ys = [mae[f"{h}|{kind}"][name] for h in range(24)]
            ax.plot(range(24), ys, style, color=FIXED[name], lw=3, label=f"{name}, {kind}")
            peak[(name, kind)] = (int(np.argmax(ys)), max(ys))
    ax.set_xticks(range(0, 24, 2), [f"{h}:00" for h in range(0, 24, 2)])
    ax.set_xlabel("Target hour of day (Chicago time)")
    ax.set_ylabel("MAE (gCO₂/kWh)")
    ax.legend(frameon=False, ncol=2)
    h, v = peak[("model", "weekday")]
    ax.set_title(f"Model errors are largest around {h}:00 on weekdays ({v:.0f} g/kWh)", loc="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    finish(fig, "04_when_wrong.png", f"test period {period}")
    hw, vw = peak[("model", "weekend")]
    return (f"The model's weekday MAE peaks at {h}:00 Chicago time ({v:.1f} gCO₂/kWh) and its "
            f"weekend MAE at {hw}:00 ({vw:.1f}).")


def fig_wind(d: dict, period: str) -> str:
    """05: day-over-day change in wind share vs the model's mean daily bias."""
    w = d["wind_vs_bias"]
    x = 100 * np.array(w["d_wind_share"])
    fig, ax = plt.subplots(figsize=SIZE)
    ax.axhline(0, color="#cccccc", lw=1)
    ax.axvline(0, color="#cccccc", lw=1)
    for name in ["persistence", "model"]:
        ax.scatter(x, w[f"bias_{name}"], s=70, color=FIXED[name], alpha=0.8,
                   label=f"{name} (r = {w[f'r_{name}']:+.2f})")
    ax.set_xlabel("Change in wind share vs the day before (percentage points)")
    ax.set_ylabel("Daily mean bias, forecast − truth (gCO₂/kWh)")
    ax.legend(frameon=False)
    r = w["r_model"]
    if r > 0:  # positive r: more wind than yesterday goes with forecasts that are too high
        ax.set_title(f"Windier than yesterday → forecast too dirty: the model can't see "
                     f"tomorrow's wind (r = {r:+.2f})", loc="left")
    else:
        ax.set_title(f"Wind change and model bias are not positively linked (r = {r:+.2f})", loc="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    finish(fig, "05_wind.png", f"test period {period}")
    return (f"Across {len(x)} test days, the day-over-day change in PJM wind share correlates "
            f"with the model's daily bias at r = {w['r_model']:.2f} (persistence r = "
            f"{w['r_persistence']:.2f})" + (": when tomorrow is windier, the forecast is too high."
                                             if w["r_model"] > 0 else "."))


def fig_flat_bottom(d: dict, period: str) -> str:
    """06: histogram of the gap between the 3rd and 6th cleanest true hour per day."""
    f = d["flat_bottom"]
    mae = d["mae_all_test_rows"]["model"]
    flat = f["median"] < mae  # the README's guess holds if the gap is below the typical error
    fig, ax = plt.subplots(figsize=SIZE)
    ax.hist(f["gap_3rd_to_6th"], bins=25, color=FIXED["truth"], alpha=0.75)
    ax.axvline(f["median"], color=FIXED["truth"], ls="--", lw=3, label=f"median gap {f['median']:.1f}")
    ax.axvline(mae, color=FIXED["model"], lw=3, label=f"model MAE {mae:.1f}")
    ax.set_xlabel("Gap between the 3rd and 6th cleanest true hour of the day (gCO₂/kWh)")
    ax.set_ylabel("Test days")
    ax.legend(frameon=False)
    verdict = "flat" if flat else "not flat"
    ax.set_title(f"The bottom of the daily curve is {verdict}: the 3rd and 6th cleanest hours\n"
                 f"differ by {f['median']:.0f} g/kWh on a typical day, less than the model's "
                 f"{mae:.0f} g/kWh error" if flat else
                 f"The bottom of the daily curve is {verdict}: median gap {f['median']:.0f} g/kWh "
                 f"vs {mae:.0f} g/kWh model error", loc="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    finish(fig, "06_flat_bottom.png", f"test period {period}")
    return (f"On a median test day the 3rd and 6th cleanest hours differ by {f['median']:.1f} "
            f"gCO₂/kWh (10th–90th percentile {f['p10']:.1f}–{f['p90']:.1f}, {f['days']} days), "
            + (f"smaller than the model's {mae:.1f} gCO₂/kWh MAE, so small errors reorder the "
               f"cleanest hours while costing the user little (model regret "
               f"{d['sensitivity']['UTC|k=3']['model']['regret']:.1f} g/kWh)."
               if flat else f"not smaller than the model's {mae:.1f} gCO₂/kWh MAE."))


def main() -> None:
    d = json.loads(OUT_PATH.read_text())
    preds = load_predictions()
    assert d["forecasts"] == [c.removeprefix("pred_") for c in pred_columns(preds)], \
        "decision_metrics.json is stale: run python -m ml.decision first"
    period = d["test_period"]
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    caps = {"01_week.png": fig_week(preds, d, period), "02_shape.png": fig_shape(d, period),
            "03_scoreboard.png": fig_scoreboard(d, period),
            "04_when_wrong.png": fig_when_wrong(d, period), "05_wind.png": fig_wind(d, period),
            "06_flat_bottom.png": fig_flat_bottom(d, period)}
    lines = ["# Figure captions", "", "Auto-written by `python -m ml.figures`; every number "
             "comes from results/decision_metrics.json.", ""]
    lines += [f"- **{k}**: {v}" for k, v in caps.items()]
    (FIG_DIR / "captions.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
