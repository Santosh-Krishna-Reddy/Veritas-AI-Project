"use client"

import { useState } from "react"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { When } from "@/components/when"
import { dayLabel, hourLabel, type Forecast } from "@/lib/api"

// Which of the 5 colour steps an hour gets: its place between the day's lowest and highest
// forecast. Display only; the numbers themselves come from the API.
function step(v: number, lo: number, hi: number): number {
  return hi === lo ? 3 : Math.min(5, 1 + Math.floor(((v - lo) / (hi - lo)) * 5))
}

type Props = { data: Forecast; active: number | null; setActive: (i: number | null) => void }

export function HourStrip({ data, active, setActive }: Props) {
  const values = data.hours.map((h) => h.forecast)
  const [lo, hi] = [Math.min(...values), Math.max(...values)]
  const rank = new Map(data.cleanest_hours.map((ts, i) => [ts, i + 1]))
  const shown = active ?? data.hours.findIndex((h) => h.ts_local === data.cleanest_hours[0])

  return (
    <div className="space-y-3">
      <ol className="grid grid-cols-8 gap-0.5 sm:grid-cols-12 lg:grid-cols-24" aria-label="Forecast for each hour, Chicago time">
        {data.hours.map((h, i) => {
          const r = rank.get(h.ts_local)
          const worst = h.ts_local === data.dirtiest_hour
          const newDay = i === 0 || hourLabel(h.ts_local) === "12 AM"
          return (
            <li key={h.ts_utc} className="flex flex-col">
              {/* Day name only where a day starts, like the date line in a tide table. */}
              <span className="h-5 font-heading text-step--1 text-ink-2" aria-hidden={!newDay}>{newDay ? dayLabel(h.ts_local) : ""}</span>
              <button
                type="button"
                onMouseEnter={() => setActive(i)}
                onMouseLeave={() => setActive(null)}
                onFocus={() => setActive(i)}
                onBlur={() => setActive(null)}
                aria-label={`${dayLabel(h.ts_local)} ${hourLabel(h.ts_local)}: ${h.forecast} grams per kilowatt-hour${r ? `, cleanest hour number ${r}` : ""}${worst ? ", dirtiest hour" : ""}`}
                style={{ background: `var(--scale-${step(h.forecast, lo, hi)})`, boxShadow: active === i ? "inset 0 -4px 0 var(--ink)" : undefined }}
                className={`flex h-14 flex-col items-center justify-center rounded-sm text-ink ${r ? "settle outline-2 outline-ink -outline-offset-2" : ""} ${worst ? "outline-2 outline-dashed outline-dirty -outline-offset-2" : ""}`}
                key={r ? `${h.ts_utc}-${data.load_kwh}` : h.ts_utc}
              >
                <span className="text-[0.75rem] leading-none"><When iso={h.ts_local} /></span>
                <span className="num mt-1 text-step--1 leading-none">{Math.round(h.forecast)}</span>
              </button>
              {/* Rank under each of the 3 cleanest cells, as under the chart's diamonds. The hour
                  you point at gets a bar inside its cell: shape, not colour, marks both. */}
              <span className="num h-5 text-center text-step--1 leading-5 font-semibold">{r ?? ""}</span>
            </li>
          )
        })}
      </ol>
      <Readout data={data} index={shown} />
      <Legend lo={lo} hi={hi} />
    </div>
  )
}

function Readout({ data, index }: { data: Forecast; index: number }) {
  const h = data.hours[index]
  const isWorst = h.ts_local === data.dirtiest_hour
  return (
    <p aria-live="polite" className="min-h-12 text-step-0">
      <span className="font-medium"><When iso={h.ts_local} day />:</span> <span className="num">{h.forecast}</span> g/kWh.{" "}
      {isWorst ? (
        "This is the dirtiest hour in the forecast."
      ) : (
        <>
          Running {data.load_kwh} kWh then instead of at <When iso={data.dirtiest_hour} /> saves{" "}
          <span key={data.load_kwh} className="settle inline-block font-semibold whitespace-nowrap"><span className="num">{h.saved_kg.toFixed(2)}</span>&#8239;kg</span> of&nbsp;CO₂.
        </>
      )}
    </p>
  )
}

function Legend({ lo, hi }: { lo: number; hi: number }) {
  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-step--1 text-ink-2">
      <span className="flex items-center gap-2">
        Cleaner <span className="num">{Math.round(lo)}</span>
        <span className="flex" aria-hidden>
          {[1, 2, 3, 4, 5].map((s) => <span key={s} className="h-3 w-5" style={{ background: `var(--scale-${s})` }} />)}
        </span>
        <span className="num">{Math.round(hi)}</span> dirtier (g/kWh)
      </span>
      <span className="flex items-center gap-2"><span className="h-3 w-5 rounded-sm outline-2 outline-ink" aria-hidden /> 3 cleanest, ranked</span>
      <span className="flex items-center gap-2"><span className="h-3 w-5 rounded-sm outline-2 outline-dashed outline-dirty" aria-hidden /> dirtiest</span>
    </div>
  )
}

export function HoursTable({ data }: { data: Forecast }) {
  const [open, setOpen] = useState(false)
  const rank = new Map(data.cleanest_hours.map((ts, i) => [ts, i + 1]))
  return (
    <div>
      <button type="button" aria-expanded={open} aria-controls="hours-table" onClick={() => setOpen(!open)}
        className="text-step--1 font-medium underline underline-offset-4">
        {open ? "Hide the table" : "Show the 24 hours as a table"}
      </button>
      {open && (
        <Table id="hours-table" className="mt-3">
          <TableHeader>
            <TableRow>
              <TableHead>Hour (Chicago)</TableHead>
              <TableHead className="text-right">Forecast g/kWh</TableHead>
              <TableHead className="text-right">Tomorrow = today</TableHead>
              <TableHead className="text-right">Saved vs dirtiest, kg</TableHead>
              <TableHead>Note</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.hours.map((h) => (
              <TableRow key={h.ts_utc}>
                <TableCell>{dayLabel(h.ts_local)} {hourLabel(h.ts_local)}</TableCell>
                <TableCell className="num text-right">{h.forecast.toFixed(1)}</TableCell>
                <TableCell className="num text-right">{h.persistence.toFixed(1)}</TableCell>
                <TableCell className="num text-right">{h.saved_kg.toFixed(3)}</TableCell>
                <TableCell>{rank.has(h.ts_local) ? `Cleanest #${rank.get(h.ts_local)}` : h.ts_local === data.dirtiest_hour ? "Dirtiest" : ""}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
