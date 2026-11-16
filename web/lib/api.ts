// Thin client for the FastAPI read-only routes. No numbers are computed in TypeScript;
// everything shown on the page comes from these responses.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export type Hour = {
  ts_utc: string
  ts_local: string
  forecast: number
  lo: number | null
  hi: number | null
  persistence: number
  saved_kg: number
}
export type Forecast = {
  issued_for_date: string
  data_through_utc: string
  filled_hours: number
  region: string
  timezone: string
  model_key: string
  load_kwh: number
  hours: Hour[]
  cleanest_hours: string[]
  dirtiest_hour: string
  co2_saved_kg: number
}
export type Score = { mae: number; cleanest_3_overlap: number }
export type Metrics = {
  metrics: Record<string, Score> & {
    _meta?: { test_period: string; test_rows: number; data_source: string }
  }
  verdict: string
}
export type FailureDay = {
  day: string
  model_mae: number
  persistence_mae: number
  true_mean: number
  bias: number
  error_type: string
  explanation: string
  hours: { ts_utc: string; true: number; model: number; persistence: number }[]
}
export type Failures = { days: FailureDay[]; pattern: string }

// "down" = could not reach the API at all; "error" = it answered with a 4xx/5xx message.
export class ApiError extends Error {
  constructor(public kind: "down" | "error", message: string) {
    super(message)
  }
}

export async function getJson<T>(path: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`)
  } catch {
    throw new ApiError("down", `Cannot reach the GridGreen API at ${API_URL}. Start it with: make api`)
  }
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    // FastAPI sends {detail: "text"} for our errors and {detail: [{msg}]} for validation.
    const d = body?.detail
    throw new ApiError("error", typeof d === "string" ? d : d?.[0]?.msg ?? `HTTP ${res.status}`)
  }
  return body as T
}

// Display helpers. They read the Chicago wall-clock time straight from the ISO string,
// so the browser's own timezone can never shift the hours.
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
export function hourLabel(iso: string): string {
  const h = Number(iso.slice(11, 13))
  return `${h % 12 || 12} ${h < 12 ? "AM" : "PM"}`
}
export function dayLabel(iso: string): string {
  return DAYS[new Date(`${iso.slice(0, 10)}T12:00:00Z`).getUTCDay()]
}
