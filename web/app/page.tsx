"use client"

import { useEffect, useState } from "react"

import { FailureChart } from "@/components/failure-chart"
import { ForecastChart } from "@/components/forecast-chart"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ApiError, dayLabel, getJson, hourLabel, type Failures, type Forecast, type Metrics } from "@/lib/api"
import { MAX_KWH, MIN_KWH, PRESETS } from "@/lib/presets"

// Each request is either done (data) or failed (error); "not yet answered" = loading.
type Result<T> = { key: string; data?: T; error?: ApiError }

function load<T>(path: string, key: string, set: (r: Result<T>) => void) {
  getJson<T>(path).then(
    (data) => set({ key, data }),
    (error: ApiError) => set({ key, error }),
  )
}

const when = (iso: string) => `${dayLabel(iso)} ${hourLabel(iso)}`

export default function Home() {
  const [kwhText, setKwhText] = useState("7")
  const [fc, setFc] = useState<Result<Forecast>>()
  const [metrics, setMetrics] = useState<Result<Metrics>>()
  const [failures, setFailures] = useState<Result<Failures>>()

  const kwh = Number(kwhText)
  const kwhValid = kwhText.trim() !== "" && Number.isFinite(kwh) && kwh >= MIN_KWH && kwh <= MAX_KWH

  useEffect(() => {
    load("/api/metrics", "m", setMetrics)
    load("/api/failures", "f", setFailures)
  }, [])

  useEffect(() => {
    if (!kwhValid) return
    // Wait until typing pauses, so we don't send one request per keystroke.
    const t = setTimeout(() => load(`/api/forecast?load_kwh=${kwh}`, kwhText, setFc), 300)
    return () => clearTimeout(t)
  }, [kwh, kwhText, kwhValid])

  const apiDown = [fc, metrics, failures].find((r) => r?.error?.kind === "down")?.error
  const fcLoading = kwhValid && fc?.key !== kwhText

  return (
    <main className="mx-auto w-full max-w-4xl space-y-6 px-4 py-8 sm:py-12">
      <header className="space-y-1">
        <p className="text-sm font-medium tracking-wide text-emerald-700 uppercase">GridGreen · PJM grid · Chicago time</p>
        <h1 className="text-2xl font-semibold sm:text-3xl">When is the grid cleanest in the next 24 hours?</h1>
      </header>

      {apiDown ? (
        <Alert variant="destructive">
          <AlertTitle>The forecast service is not running</AlertTitle>
          <AlertDescription>{apiDown.message}. Nothing is shown until it answers, so no number on this page is ever made up.</AlertDescription>
        </Alert>
      ) : (
        <>
          <Answer fc={fc} loading={fcLoading} />
          <LoadInput kwhText={kwhText} setKwhText={setKwhText} kwhValid={kwhValid} />
          <ForecastSection fc={fc} loading={fcLoading} />
          <TrustSection metrics={metrics} />
          <FailureSection failures={failures} />
        </>
      )}
      <Footer />
    </main>
  )
}

function Answer({ fc, loading }: { fc?: Result<Forecast>; loading: boolean }) {
  if (fc?.error) {
    const missing = fc.error.message.includes("not trained") || fc.error.message.includes("make data")
    return (
      <Alert variant="destructive">
        <AlertTitle>{missing ? "The model or data is missing" : "The forecast request failed"}</AlertTitle>
        <AlertDescription>{fc.error.message}</AlertDescription>
      </Alert>
    )
  }
  if (!fc?.data || loading) return <Skeleton className="h-24 w-full" />
  const d = fc.data
  return (
    <section aria-live="polite" className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
      <p className="text-xl leading-snug font-semibold text-emerald-950 sm:text-2xl">
        Run it at {d.cleanest_hours.map(when).join(", ")} (cleanest first). Moving {d.load_kwh} kWh there from the
        dirtiest hour ({when(d.dirtiest_hour)}) saves about {d.co2_saved_kg.toFixed(2)} kg of CO₂.
      </p>
      <p className="mt-2 text-sm text-emerald-900">
        Forecast for {when(d.hours[0].ts_local)} → {when(d.hours[23].ts_local)} Chicago time, the 24 hours after our
        latest grid data ({d.data_through_utc.slice(0, 16).replace("T", " ")} UTC). Region: {d.region}.
      </p>
    </section>
  )
}

function LoadInput({ kwhText, setKwhText, kwhValid }: { kwhText: string; setKwhText: (s: string) => void; kwhValid: boolean }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="space-y-1">
          <label htmlFor="kwh" className="text-sm font-medium">Load to shift (kWh)</label>
          <Input id="kwh" type="number" inputMode="decimal" min={MIN_KWH} max={MAX_KWH} step={0.5} value={kwhText}
            onChange={(e) => setKwhText(e.target.value)} aria-invalid={!kwhValid} aria-describedby="kwh-help" className="w-32" />
        </div>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <Button key={p.label} variant={Number(kwhText) === p.kwh ? "default" : "outline"} onClick={() => setKwhText(String(p.kwh))}>
              {p.label} · {p.kwh} kWh
            </Button>
          ))}
        </div>
      </CardContent>
      <p id="kwh-help" className={`px-6 text-sm ${kwhValid ? "text-muted-foreground" : "font-medium text-red-700"}`}>
        {kwhValid ? "Preset sizes are illustrative round numbers, not measurements." : `Enter a number from ${MIN_KWH} to ${MAX_KWH} kWh.`}
      </p>
    </Card>
  )
}

function ForecastSection({ fc, loading }: { fc?: Result<Forecast>; loading: boolean }) {
  if (fc?.error) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle>The next 24 hours</CardTitle>
        <CardDescription>
          Forecast carbon intensity (green) vs. the simple guess “tomorrow = today” (grey, dashed). Diamonds mark the
          three cleanest forecast hours, numbered 1–3 (1 = cleanest).
          {fc?.data && !fc.data.hours.some((h) => h.lo != null) && " No uncertainty band yet: this model gives one number per hour."}
        </CardDescription>
      </CardHeader>
      <CardContent>{!fc?.data || loading ? <Skeleton className="h-[320px] w-full" /> : <ForecastChart data={fc.data} />}</CardContent>
    </Card>
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
    <Card>
      <CardHeader>
        <CardTitle>How far to trust this</CardTitle>
        <CardDescription>
          {m ? `Scored on ${m.metrics._meta?.test_period ?? "the test period"} (${m.metrics._meta?.test_rows ?? "?"} hours) — data the model never saw while training.` : "Held-out test results."}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {metrics?.error && <Alert variant="destructive"><AlertTitle>No test results</AlertTitle><AlertDescription>{metrics.error.message}</AlertDescription></Alert>}
        {!metrics && <Skeleton className="h-40 w-full" />}
        {m && (
          <>
            <p className="font-medium">{m.verdict}</p>
            <Table>
              <TableHeader>
                <TableRow><TableHead>Method</TableHead><TableHead className="text-right">MAE</TableHead><TableHead className="text-right">Overlap</TableHead></TableRow>
              </TableHeader>
              <TableBody>
                {ROWS.filter(([k]) => m.metrics[k]).map(([k, label]) => (
                  <TableRow key={k} className={k === "model" ? "font-semibold" : ""}>
                    <TableCell className="whitespace-normal">{label}</TableCell>
                    <TableCell className="text-right tabular-nums">{m.metrics[k].mae.toFixed(2)}</TableCell>
                    <TableCell className="text-right tabular-nums">{m.metrics[k].cleanest_3_overlap.toFixed(3)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <p className="text-sm text-muted-foreground">
              MAE: average miss in gCO₂/kWh (lower is better). Overlap: share of the true 3 cleanest hours each method
              picked, averaged over test days (higher is better).
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function FailureSection({ failures }: { failures?: Result<Failures> }) {
  const worst = failures?.data?.days[0]
  return (
    <Card>
      <CardHeader>
        <CardTitle>Where it fails</CardTitle>
        <CardDescription>{worst ? `Our worst test day: ${dayLabel(worst.day)} ${worst.day} (UTC day).` : "The worst day in the test period."}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {failures?.error && <Alert variant="destructive"><AlertTitle>No failure analysis</AlertTitle><AlertDescription>{failures.error.message}</AlertDescription></Alert>}
        {!failures && <Skeleton className="h-60 w-full" />}
        {worst && (
          <>
            <p>
              The model missed by <strong>{worst.model_mae} gCO₂/kWh</strong> on average that day (persistence:{" "}
              {worst.persistence_mae}). {worst.explanation}
            </p>
            <FailureChart day={worst} />
            <p className="text-sm text-muted-foreground">{failures?.data?.pattern}</p>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function Footer() {
  return (
    <footer className="space-y-1 border-t pt-4 text-xs text-muted-foreground">
      <p>
        Data: <a className="underline" href="https://www.eia.gov/electricity/gridmonitor/">EIA-930 Hourly Electric Grid Monitor</a> (PJM),
        CO₂ factors from <a className="underline" href="https://www.eia.gov/tools/faqs/faq.php?id=74">EIA (2023)</a>, weather from{" "}
        <a className="underline" href="https://open-meteo.com/">Open-Meteo</a> (CC BY 4.0).
      </p>
      <p>Direct emissions, national average factors, one region. A student prototype, not official grid data.</p>
    </footer>
  )
}
