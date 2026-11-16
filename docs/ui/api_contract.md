# GridGreen historical replay API contract

The `/api/*` routes expose committed held-out evaluation artifacts for a read-only
dashboard. Integration note (Nov 15): the live-dashboard routes added by WEB-DESIGN own
`/api/metrics` and `/api/failures`; the replay contract's committed-artifact views are
namespaced under `/api/replay/metrics` and `/api/replay/failures` so both clients can run
against one process. They do not retrain the model and must never be presented as live or
prospective operational forecasts.

Local base URL: `http://localhost:8000`

Development CORS is allowed only for `http://localhost[:port]` and
`http://127.0.0.1[:port]` (any local port, so `next dev` can run on 3001 when 3000 is
busy). No production or LAN origin is allowed, and credentials are not enabled.

All carbon-intensity values (`forecast`, `persistence`, and `observed`) are numbers in
gCO2/kWh. All calculations, including recommendation ranking and the modeled kg
difference, are performed by the Python API.

## `GET /api/replay/dates`

Returns the UTC calendar dates that contain exactly 24 chronological, finite target
rows in `results/test_predictions.csv`.

Response shape:

| Field | Type | Meaning |
|---|---|---|
| `dates_utc` | `string[]` | Ascending `YYYY-MM-DD` UTC dates; each date is safe to pass to `/api/replay`. |

The current committed file produces 105 dates from `2026-08-01` through
`2026-11-13`. The incomplete `2026-11-14` UTC day is intentionally excluded.

Real response excerpt generated from the repository:

```json
{
  "dates_utc": [
    "2026-08-01",
    "2026-08-02",
    "2026-08-03",
    "2026-08-04",
    "2026-08-05",
    "2026-08-06",
    "2026-08-07",
    "2026-08-08",
    "2026-08-09",
    "2026-08-10"
  ]
}
```

The excerpt shows the first 10 items; clients receive all 105.

## `GET /api/replay?date=YYYY-MM-DD&load_kwh=7`

`date` is required and must be one of the dates returned by `/api/replay/dates`.
`load_kwh` is optional, defaults to `7`, and must be finite and in the inclusive range
`0..200`.

Response shape:

| Field | Type | Meaning |
|---|---|---|
| `mode` | `"historical_replay"` | Identifies this as held-out historical data, not a live forecast. |
| `region` | `string` | Region copied from the Python project configuration. |
| `utc_day` | `string` | Requested UTC day in `YYYY-MM-DD` form. |
| `display_timezone` | `"America/Chicago"` | IANA zone used for every `ts_local`. |
| `hours` | `Hour[24]` | Exactly 24 objects, ordered from UTC hour 00 through 23. |
| `recommended_indices` | `integer[3]` | Indices of the three lowest `forecast` values, cleanest first. |
| `dirtiest_index` | `integer` | Index of the highest `forecast` value. |
| `modeled_difference_kg` | `number` | `load_kwh * (dirtiest forecast - cleanest forecast) / 1000`, rounded to 3 decimals. |
| `disclaimer` | `string` | Required scope warning for the modeled comparison. |

Each `Hour` has exactly these fields:

| Field | Type | Meaning |
|---|---|---|
| `ts_utc` | ISO 8601 string | Target timestamp in UTC, including `+00:00`. |
| `ts_local` | ISO 8601 string | Same instant in `America/Chicago`, including the applicable UTC offset. |
| `forecast` | number | Existing `pred_model` value in gCO2/kWh. |
| `persistence` | number | Existing `pred_persistence` value in gCO2/kWh. |
| `observed` | number | Existing held-out `target` value in gCO2/kWh. It is shown for retrospective evaluation only and is not forecast input. |

Real response excerpt for `GET /api/replay?date=2026-08-01&load_kwh=7`:

```json
{
  "mode": "historical_replay",
  "region": "PJM (Chicago / mid-Atlantic grid)",
  "utc_day": "2026-08-01",
  "display_timezone": "America/Chicago",
  "hours": [
    {
      "ts_utc": "2026-08-01T00:00:00+00:00",
      "ts_local": "2026-07-31T19:00:00-05:00",
      "forecast": 384.05511273162733,
      "persistence": 391.46981576309514,
      "observed": 389.8852339577892
    },
    {
      "ts_utc": "2026-08-01T01:00:00+00:00",
      "ts_local": "2026-07-31T20:00:00-05:00",
      "forecast": 397.069921407018,
      "persistence": 403.3995612958402,
      "observed": 398.4862682897815
    },
    {
      "ts_utc": "2026-08-01T23:00:00+00:00",
      "ts_local": "2026-08-01T18:00:00-05:00",
      "forecast": 370.2366651236795,
      "persistence": 377.71836958425007,
      "observed": 356.04544670930034
    }
  ],
  "recommended_indices": [15, 14, 13],
  "dirtiest_index": 3,
  "modeled_difference_kg": 0.518,
  "disclaimer": "This is a retrospective average-intensity comparison, not a live operational forecast or verified marginal avoided emissions."
}
```

The example abbreviates `hours` for readability; the actual response always contains
all 24 objects. Array indices are zero-based positions in that 24-object array. Ties in
the cleanest ranking are resolved by lower index; a tie for dirtiest also uses the
lower index. A zero `load_kwh` returns `modeled_difference_kg: 0` without changing the
rankings.

## `GET /api/replay/metrics`

Returns the committed JSON objects without recomputing or relabeling their contents.

Response shape:

| Field | Type | Source |
|---|---|---|
| `evaluation_metrics` | object | `results/metrics.json` |
| `decision_metrics` | object | `results/decision_metrics.json` |

Real response excerpt:

```json
{
  "evaluation_metrics": {
    "persistence": {
      "mae": 16.937007694349827,
      "cleanest_3_overlap": 0.4825396825396825
    },
    "model": {
      "mae": 13.768439399947058,
      "cleanest_3_overlap": 0.473015873015873
    },
    "_meta": {
      "region": "PJM (Chicago / mid-Atlantic grid)",
      "test_period": "2026-08-01 to 2026-11-14",
      "test_rows": 2529,
      "data_source": "real"
    }
  },
  "decision_metrics": {
    "_scope": "Retrospective held-out analysis; not a prospective real-time forecast test.",
    "source": "results/test_predictions.csv",
    "rows": 2529,
    "full_utc_days": 105
  }
}
```

The response includes every additional key present in both committed files; the
excerpt shows representative real values only.

## `GET /api/replay/failures`

Returns records parsed from the generated table in `results/failures.md`. The API does
not infer causes or add values beyond that report.

Available response shape:

| Field | Type | Meaning |
|---|---|---|
| `status` | `"available"` | Structured committed evidence was found. |
| `source` | string | Repository-relative committed source path. |
| `records` | `FailureRecord[]` | Grounded table rows in their committed order. |

Each `FailureRecord` contains `utc_day` and `weekday` strings;
`model_mae_gco2_per_kwh`, `persistence_mae_gco2_per_kwh`, and
`average_observed_gco2_per_kwh` numbers; and the committed `error_type` and `evidence`
strings.

Real response excerpt:

```json
{
  "status": "available",
  "source": "results/failures.md",
  "records": [
    {
      "utc_day": "2026-10-14",
      "weekday": "Wed",
      "model_mae_gco2_per_kwh": 30.0,
      "persistence_mae_gco2_per_kwh": 36.0,
      "average_observed_gco2_per_kwh": 411.0,
      "error_type": "level offset",
      "evidence": "-30 g all day; temp_c 24 -> 19 (1.02x test avg); wind_share 6.4% -> 3.3% (1.16x test avg)"
    }
  ]
}
```

The current response contains five records. If the committed Markdown exists but no
structured failure table is available, the explicit response is:

```json
{
  "status": "unavailable",
  "source": "results/failures.md",
  "records": [],
  "reason": "No structured failure records were available in the committed report."
}
```

## Errors

FastAPI errors use `{"detail": "message"}` unless request parsing fails before the
route runs.

| Status | Condition |
|---|---|
| `404` | The date is validly formatted but is not a complete replay day. |
| `422` | Missing/malformed date, nonnumeric/nonfinite load, or load outside `0..200`. |
| `503` | A required committed CSV, JSON, or Markdown file is missing, unreadable, or structurally invalid. |

Examples:

```json
{"detail":"date must use YYYY-MM-DD format"}
```

```json
{"detail":"no complete 24-hour historical replay for 2026-11-14"}
```

## Existing routes

`GET /health` and `POST /predict` retain their existing request and response behavior.
The replay routes read existing `pred_model` and `pred_persistence` values only; they do
not invoke training and do not use target-day observations as model input.
