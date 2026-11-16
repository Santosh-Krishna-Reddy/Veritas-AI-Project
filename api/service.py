"""Read committed evaluation artifacts for the historical replay API."""

from __future__ import annotations

import json
import math
import re
from datetime import date as date_type
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from ml import config as C

PREDICTIONS_PATH = C.RESULTS_DIR / "test_predictions.csv"
METRICS_PATH = C.RESULTS_DIR / "metrics.json"
DECISION_METRICS_PATH = C.RESULTS_DIR / "decision_metrics.json"
FAILURES_PATH = C.RESULTS_DIR / "failures.md"

DISPLAY_TIMEZONE = "America/Chicago"
REQUIRED_PREDICTION_COLUMNS = (
    "target_timestamp",
    "target",
    "pred_persistence",
    "pred_model",
)
REPLAY_DISCLAIMER = (
    "This is a retrospective average-intensity comparison, not a live operational "
    "forecast or verified marginal avoided emissions."
)


class ReplayDataUnavailable(RuntimeError):
    """Raised when a required committed result cannot be read reliably."""


class InvalidReplayDate(ValueError):
    """Raised when a replay date is not in the required YYYY-MM-DD form."""


class ReplayDateNotFound(LookupError):
    """Raised when a requested date is not a complete committed UTC day."""


class InvalidReplayLoad(ValueError):
    """Raised when load_kwh is not finite or is outside the supported range."""


def _display_path(path: Path) -> str:
    """Return a repository-relative path for an API error message."""
    try:
        return str(path.relative_to(C.ROOT))
    except ValueError:
        return str(path)


def _read_predictions() -> pd.DataFrame:
    """Load and validate columns and scalar types used by replay responses."""
    try:
        frame = pd.read_csv(PREDICTIONS_PATH)
    except (OSError, UnicodeError, pd.errors.ParserError) as exc:
        name = _display_path(PREDICTIONS_PATH)
        raise ReplayDataUnavailable(f"required replay data unavailable: {name}: {exc}") from exc

    missing = sorted(set(REQUIRED_PREDICTION_COLUMNS) - set(frame.columns))
    if missing:
        name = _display_path(PREDICTIONS_PATH)
        raise ReplayDataUnavailable(
            f"required replay data unavailable: {name} is missing columns: {', '.join(missing)}"
        )

    clean = frame[list(REQUIRED_PREDICTION_COLUMNS)].copy()
    clean["target_timestamp"] = pd.to_datetime(
        clean["target_timestamp"], utc=True, errors="coerce"
    )
    for column in ("target", "pred_persistence", "pred_model"):
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    return clean


def _complete_days(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return only UTC days containing each of their 24 finite hourly rows."""
    valid = frame.dropna(subset=list(REQUIRED_PREDICTION_COLUMNS)).copy()
    finite = valid[["target", "pred_persistence", "pred_model"]].apply(
        lambda column: column.map(math.isfinite)
    )
    valid = valid[finite.all(axis=1)]
    valid["utc_day"] = valid["target_timestamp"].dt.strftime("%Y-%m-%d")

    complete: dict[str, pd.DataFrame] = {}
    for utc_day, group in valid.groupby("utc_day", sort=True):
        ordered = group.sort_values("target_timestamp").reset_index(drop=True)
        expected = pd.date_range(f"{utc_day}T00:00:00Z", periods=24, freq="h")
        actual = pd.DatetimeIndex(ordered["target_timestamp"])
        if len(ordered) == 24 and actual.equals(expected):
            complete[str(utc_day)] = ordered
    return complete


def available_replay_dates() -> list[str]:
    """Return UTC dates backed by exactly 24 complete committed result rows."""
    return list(_complete_days(_read_predictions()).keys())


def _validated_day(value: str) -> str:
    """Validate the exact calendar-date syntax used by the replay endpoint."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InvalidReplayDate("date must use YYYY-MM-DD format")
    try:
        parsed = date_type.fromisoformat(value)
    except ValueError as exc:
        raise InvalidReplayDate("date must be a valid UTC calendar date") from exc
    return parsed.isoformat()


def _validated_load(value: float) -> float:
    """Validate the supported flexible-load interval."""
    if not math.isfinite(value) or not 0 <= value <= 200:
        raise InvalidReplayLoad("load_kwh must be finite and between 0 and 200")
    return float(value)


def historical_replay(utc_day: str, load_kwh: float) -> dict:
    """Build a 24-hour retrospective replay from committed test predictions."""
    day = _validated_day(utc_day)
    load = _validated_load(load_kwh)
    complete = _complete_days(_read_predictions())
    if day not in complete:
        raise ReplayDateNotFound(f"no complete 24-hour historical replay for {day}")

    rows = complete[day]
    forecast = rows["pred_model"].astype(float).tolist()
    recommended = sorted(range(24), key=lambda index: (forecast[index], index))[:3]
    dirtiest = max(range(24), key=lambda index: forecast[index])
    difference_kg = load * (forecast[dirtiest] - forecast[recommended[0]]) / 1000
    local_zone = ZoneInfo(DISPLAY_TIMEZONE)

    hours = []
    for row in rows.itertuples(index=False):
        timestamp = row.target_timestamp.to_pydatetime()
        hours.append(
            {
                "ts_utc": timestamp.isoformat(),
                "ts_local": timestamp.astimezone(local_zone).isoformat(),
                "forecast": float(row.pred_model),
                "persistence": float(row.pred_persistence),
                "observed": float(row.target),
            }
        )

    return {
        "mode": "historical_replay",
        "region": C.REGION_NAME,
        "utc_day": day,
        "display_timezone": DISPLAY_TIMEZONE,
        "hours": hours,
        "recommended_indices": recommended,
        "dirtiest_index": dirtiest,
        "modeled_difference_kg": round(float(difference_kg), 3),
        "disclaimer": REPLAY_DISCLAIMER,
    }


def _read_json_object(path: Path) -> dict:
    """Read one required committed JSON object or report it unavailable."""
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        name = _display_path(path)
        raise ReplayDataUnavailable(f"required metrics unavailable: {name}: {exc}") from exc
    if not isinstance(value, dict):
        name = _display_path(path)
        raise ReplayDataUnavailable(f"required metrics unavailable: {name} is not a JSON object")
    return value


def committed_metrics() -> dict:
    """Return the two committed evaluation files without recalculation."""
    return {
        "evaluation_metrics": _read_json_object(METRICS_PATH),
        "decision_metrics": _read_json_object(DECISION_METRICS_PATH),
    }


def _failure_record(cells: list[str]) -> dict | None:
    """Convert one generated Markdown table row without adding interpretation."""
    if len(cells) != 7:
        return None
    try:
        return {
            "utc_day": _validated_day(cells[0]),
            "weekday": cells[1],
            "model_mae_gco2_per_kwh": float(cells[2]),
            "persistence_mae_gco2_per_kwh": float(cells[3]),
            "average_observed_gco2_per_kwh": float(cells[4]),
            "error_type": cells[5],
            "evidence": cells[6],
        }
    except (InvalidReplayDate, ValueError):
        return None


def _parse_failure_records(markdown: str) -> list[dict]:
    """Extract grounded records from the generated failures table."""
    lines = markdown.splitlines()
    header = (
        "| Day | Weekday | Model MAE | Persistence MAE | Avg true gCO2/kWh | "
        "Error type | Why |"
    )
    try:
        start = lines.index(header) + 2
    except ValueError:
        return []

    records = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        record = _failure_record(cells)
        if record is not None:
            records.append(record)
    return records


def committed_failures() -> dict:
    """Return failure evidence parsed only from the committed generated report."""
    try:
        markdown = FAILURES_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        name = _display_path(FAILURES_PATH)
        raise ReplayDataUnavailable(
            f"required failure evidence unavailable: {name}: {exc}"
        ) from exc

    records = _parse_failure_records(markdown)
    if not records:
        return {
            "status": "unavailable",
            "source": _display_path(FAILURES_PATH),
            "records": [],
            "reason": "No structured failure records were available in the committed report.",
        }
    return {
        "status": "available",
        "source": _display_path(FAILURES_PATH),
        "records": records,
    }
