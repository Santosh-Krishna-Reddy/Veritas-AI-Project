"use client"

import { useEffect, useState } from "react"

import { FailureChart } from "@/components/failure-chart"
import { ForecastChart, LineKey } from "@/components/forecast-chart"
import { HourStrip, HoursTable } from "@/components/hour-strip"
import { When } from "@/components/when"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ApiError, dayLabel, getJson, type Failures, type Forecast, type Metrics } from "@/lib/api"
import { MAX_KWH, MIN_KWH, PRESETS } from "@/lib/presets"

// Each request is either done (data) or failed (error); "not yet answered" = loading.
type Result<T> = { key: string; data?: T; error?: ApiError }

function load<T>(path: string, key: string, set: (r: Result<T>) => void) {
  getJson<T>(path).then(
    (data) => set({ key, data }),
    (error: ApiError) => set({ key, error }),
  )
}

const DAY_NAMES: Record<string, string> = { Sun: "Sunday", Mon: "Monday", Tue: "Tuesday", Wed: "Wednesday", Thu: "Thursday", Fri: "Friday", Sat: "Saturday" }
const H2 = "font-heading text-step-1 font-semibold"

export default function Home() {
  const [kwhText, setKwhText] = useState("7")
  const [fc, setFc] = useState<Result<Forecast>>()
  const [metrics, setMetrics] = useState<Result<Metrics>>()
  const [failures, setFailures] = useState<Result<Failures>>()
  const [active, setActive] = useState<number | null>(null) // hour pointed at, shared by chart and strip

  const kwh = Number(kwhText)
  const kwhValid = kwhText.trim() !== "" && Number.isFinite(kwh) && kwh >= MIN_KWH && kwh <= MAX_KWH

  useEffect(() => {
    load("/api/metrics", "m", setMetrics)
    load("/api/failures", "f", setFailures)
  }, [])

  useEffect(() => {
    if (!kwhValid) return
    // Wait until typing pauses, so we don't send one request per keystroke. When the load
    // changes again, `live` turns false, so a slower, older answer can never overwrite a newer one.
    let live = true
    const t = setTimeout(() => load<Forecast>(`/api/forecast?load_kwh=${kwh}`, kwhText, (r) => live && setFc(r)), 300)
    return () => {
      live = false
      clearTimeout(t)
    }
  }, [kwh, kwhText, kwhValid])

  const apiDown = [fc, metrics, failures].find((r) => r?.error?.kind === "down")?.error

  return (
    <main className="mx-auto w-full max-w-[66rem] px-5 pt-6 pb-12 sm:px-8 sm:pt-8">
      <header className="mb-6 flex flex-wrap items-baseline gap-x-3 border-b border-rule pb-3">
        <span className="font-heading text-step-1 font-semibold">GridGreen</span>
        <span className="text-step--1 text-ink-2">Cleanest hours on the PJM grid, in Chicago time</span>
      </header>

      {apiDown ? (
        <Alert variant="destructive" className="mb-8">
          <AlertTitle>The forecast service is not running</AlertTitle>
          <AlertDescription>{apiDown.message}, then reload this page. Nothing else is shown until the service answers.</AlertDescription>
        </Alert>
      ) : (
        <>
          <Answer fc={fc} />
          <LoadInput kwhText={kwhText} setKwhText={setKwhText} kwhValid={kwhValid} />
          <HourByHour fc={fc} active={active} setActive={setActive} />
          <TrustSection metrics={metrics} />
          <FailureSection failures={failures} />
        </>
      )}
      <Footer />
    </main>
  )
}

function Answer({ fc }: { fc?: Result<Forecast> }) {
  if (fc?.error) {
    const missing = fc.error.message.includes("not trained") || fc.error.message.includes("make data")
    return (
      <Alert variant="destructive" className="mb-6">
        <AlertTitle>{missing ? "The model or data is missing" : "The forecast request failed"}</AlertTitle>
        <AlertDescription>{fc.error.message}</AlertDescription>
      </Alert>
    )
  }
  // Skeleton on first load only; later loads keep the old answer until the new one lands.
  if (!fc?.data) return <Skeleton className="mb-6 h-32 w-full" />
  const d = fc.data
  const days = new Set(d.cleanest_hours.map(dayLabel))
  // One day: name it once at the end. Spanning midnight: put the day on each hour.
  const [a, b, c] = d.cleanest_hours.map((iso) => <When key={iso} iso={iso} day={days.size > 1} />)
  return (
    <section aria-live="polite" className="mb-6 space-y-3">
      <h1 className="font-heading text-[clamp(var(--step-2),1rem+2.2vw,var(--step-4))] leading-[1.1] font-semibold text-balance">
        Run it at {a}, {b} or {c}
        {days.size === 1 && ` on ${DAY_NAMES[[...days][0]]}`} (cleanest first).
      </h1>
      <p className="max-w-[60ch] text-step-1 leading-snug text-pretty">
        Moving <span className="num">{d.load_kwh}</span> kWh there from the dirtiest hour (
        <When iso={d.dirtiest_hour} day />) saves about{" "}
        <span key={d.load_kwh} className="settle inline-block font-semibold whitespace-nowrap"><span className="num">{d.co2_saved_kg.toFixed(2)}</span>&#8239;kg</span> of&nbsp;CO₂.
      </p>
      <p className="max-w-[70ch] text-step--1 text-ink-2">
        Forecast for <When iso={d.hours[0].ts_local} day /> to <When iso={d.hours[23].ts_local} day /> Chicago time. Latest real
        grid data: <span className="num whitespace-nowrap">{d.data_through_utc.slice(0, 16).replace("T", " ")}</span> UTC
        {d.filled_hours > 0 && <>; the <span className="num">{d.filled_hours}</span> hours after it are filled in by repeating the last value</>}. Region: {d.region}.
      </p>
    </section>
  )
}

function LoadInput({ kwhText, setKwhText, kwhValid }: { kwhText: string; setKwhText: (s: string) => void; kwhValid: boolean }) {
  return (
    <section className="mb-8 flex flex-col gap-2" aria-label="Load">
      <div className="flex flex-wrap items-end gap-x-4 gap-y-3">
        <label className="flex flex-col gap-1">
          <span className="text-step--1 font-medium">Energy your appliance will use</span>
          <span className="flex items-center gap-2">
            <Input type="number" inputMode="decimal" min={MIN_KWH} max={MAX_KWH} step={0.5} value={kwhText}
              onChange={(e) => setKwhText(e.target.value)} aria-invalid={!kwhValid} aria-describedby="kwh-help"
              className="num h-9 w-24 text-right text-step-0 md:text-step-0" />
            <span className="text-step-0">kWh</span>
          </span>
        </label>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Set the energy for a typical load">
          {PRESETS.map((p) => (
            <button key={p.label} type="button" aria-pressed={Number(kwhText) === p.kwh} onClick={() => setKwhText(String(p.kwh))}
              className="h-9 rounded-sm border border-rule px-3 text-step--1 hover:border-ink aria-pressed:border-ink aria-pressed:bg-ink aria-pressed:text-paper">
              {p.label} <span className="num">{p.kwh}</span> kWh
            </button>
          ))}
        </div>
      </div>
      <p id="kwh-help" className={`text-step--1 ${kwhValid ? "text-ink-2" : "font-medium text-dirty"}`}>
        {kwhValid ? "The buttons use typical round numbers, not measurements. Type your own if you know it." : `Enter a number from ${MIN_KWH} to ${MAX_KWH} kWh.`}
      </p>
    </section>
  )
}

function HourByHour({ fc, active, setActive }: { fc?: Result<Forecast>; active: number | null; setActive: (i: number | null) => void }) {
  if (fc?.error) return null
  const d = fc?.data
  return (
    <section className="mb-12 space-y-3" aria-labelledby="hours-h">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h2 id="hours-h" className={H2}>Hour by hour</h2>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-step--1 text-ink-2">
          <LineKey color="var(--clean)">Our forecast, g/kWh</LineKey>
          <LineKey color="var(--ink-2)" dashed>Tomorrow = today</LineKey>
          {d && !d.hours.some((h) => h.lo != null) && <span>No uncertainty band yet: this model gives one number per hour.</span>}
        </div>
      </div>
      {!d ? <Skeleton className="h-[360px] w-full" /> : (
        <>
          <ForecastChart data={d} active={active} setActive={setActive} />
          <HourStrip data={d} active={active} setActive={setActive} />
          <HoursTable data={d} />
        </>
      )}
    </section>
  )
}

const ROWS: [string, string][] = [
  ["persistence", "Persistence: tomorrow = today"],
  ["last_week", "Same hour last week"],
  ["model_lags_only", "Model, past carbon only"],
  ["model", "GridGreen model (+ fuel mix & weather)"],
]

function TrustSection({ metrics }: { metrics?: Result<Metrics> }) {
  const m = metrics?.data
  return (
    <section className="mb-12 space-y-3 border-t border-rule pt-6" aria-labelledby="trust-h">
      <h2 id="trust-h" className={H2}>How far to trust this</h2>
      {metrics?.error && <Alert variant="destructive"><AlertTitle>No test results</AlertTitle><AlertDescription>{metrics.error.message}</AlertDescription></Alert>}
      {!metrics && <Skeleton className="h-40 w-full" />}
      {m && (
        <>
          <p className="text-step--1 text-ink-2">
            Scored on <span className="num">{m.metrics._meta?.test_period ?? "the test period"}</span> (
            <span className="num">{m.metrics._meta?.test_rows ?? "?"}</span> hours) — data the model never saw while training.
          </p>
          <p className="max-w-[70ch] font-medium">{m.verdict}</p>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Method</TableHead><TableHead className="text-right">MAE</TableHead><TableHead className="text-right">Overlap</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {ROWS.filter(([k]) => m.metrics[k]).map(([k, label]) => (
                <TableRow key={k} className={k === "model" ? "font-semibold" : ""}>
                  <TableCell className="whitespace-normal">{label}</TableCell>
                  <TableCell className="num text-right">{m.metrics[k].mae.toFixed(2)}</TableCell>
                  <TableCell className="num text-right">{m.metrics[k].cleanest_3_overlap.toFixed(3)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <p className="max-w-[70ch] text-step--1 text-ink-2">
            MAE: average miss in gCO₂/kWh (lower is better). Overlap: share of the true 3 cleanest hours each method
            picked, averaged over test days (higher is better).
          </p>
        </>
      )}
    </section>
  )
}

function FailureSection({ failures }: { failures?: Result<Failures> }) {
  const worst = failures?.data?.days[0]
  return (
    <section className="mb-12 space-y-3 border-t border-rule pt-6" aria-labelledby="fail-h">
      <h2 id="fail-h" className={H2}>Where it fails</h2>
      {failures?.error && <Alert variant="destructive"><AlertTitle>No failure analysis</AlertTitle><AlertDescription>{failures.error.message}</AlertDescription></Alert>}
      {!failures && <Skeleton className="h-60 w-full" />}
      {worst && (
        <>
          <p className="text-step--1 text-ink-2">Our worst test day: {dayLabel(worst.day)} <span className="num">{worst.day}</span> (UTC day).</p>
          <p className="max-w-[70ch]">
            The model missed by <strong className="num">{worst.model_mae} gCO₂/kWh</strong> on average that day (persistence:{" "}
            <span className="num">{worst.persistence_mae}</span>). {worst.explanation}
          </p>
          <FailureChart day={worst} />
          <p className="max-w-[70ch] text-step--1 text-ink-2">{failures?.data?.pattern}</p>
        </>
      )}
    </section>
  )
}

function Footer() {
  return (
    <footer className="space-y-1 border-t border-rule pt-4 text-step--1 text-ink-2">
      <p>
        Data: <a className="underline" href="https://www.eia.gov/electricity/gridmonitor/">EIA-930 Hourly Electric Grid Monitor</a> (PJM),
        CO₂ factors from <a className="underline" href="https://www.eia.gov/tools/faqs/faq.php?id=74">EIA (2023)</a>, weather from{" "}
        <a className="underline" href="https://open-meteo.com/">Open-Meteo</a> (CC BY 4.0).
      </p>
      <p>Direct emissions, national average factors, one region. A student prototype, not official grid data.</p>
    </footer>
  )
}
