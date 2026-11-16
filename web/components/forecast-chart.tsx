"use client"

import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts"

import { ChartContainer, type ChartConfig } from "@/components/ui/chart"
import { AxisTick } from "@/components/when"
import { dayLabel, hourLabel, type Forecast } from "@/lib/api"

const config = {
  forecast: { label: "Our forecast", color: "var(--clean)" },
  persistence: { label: "Tomorrow = today", color: "var(--ink-2)" },
  band: { label: "10–90 % range", color: "var(--clean)" },
} satisfies ChartConfig

const tick = { fontFamily: "var(--font-plex-mono)", fontSize: "0.75rem", fill: "var(--ink-2)" }
type DotProps = { cx?: number; cy?: number; index?: number }
type Props = { data: Forecast; active: number | null; setActive: (i: number | null) => void }

export function ForecastChart({ data, active, setActive }: Props) {
  const rows = data.hours.map((h) => ({
    label: `${dayLabel(h.ts_local)} ${hourLabel(h.ts_local)}`,
    forecast: h.forecast,
    persistence: h.persistence,
    band: h.lo != null && h.hi != null ? [h.lo, h.hi] : null,
  }))
  const hasBand = rows.some((r) => r.band)
  // Rank (1 = cleanest) for each of the 3 cleanest hours, keyed by hour index.
  const rank = new Map(data.cleanest_hours.map((ts, i) => [data.hours.findIndex((h) => h.ts_local === ts), i + 1]))

  // Cleanest hours get a diamond plus a rank number, so colour is never the only cue.
  const dot = ({ cx, cy, index }: DotProps) => {
    const r = index != null ? rank.get(index) : undefined
    if (r == null || cx == null || cy == null) return <g key={index} />
    return (
      <g key={index}>
        <path d={`M${cx},${cy - 7}L${cx + 7},${cy}L${cx},${cy + 7}L${cx - 7},${cy}Z`} fill="var(--clean)" stroke="var(--paper)" strokeWidth={1.5} />
        <text x={cx} y={cy + 21} textAnchor="middle" style={{ ...tick, fill: "var(--ink)", fontWeight: 600 }}>{r}</text>
      </g>
    )
  }

  return (
    <ChartContainer config={config} className="aspect-auto h-[15rem] w-full" role="img"
      aria-label="Line chart of the 24-hour forecast; the same numbers are in the hour strip and the table below.">
      <ComposedChart data={rows} margin={{ top: 8, right: 28, bottom: 0, left: 0 }}
        onMouseMove={(s) => setActive(s.activeTooltipIndex == null ? null : Number(s.activeTooltipIndex))}
        onMouseLeave={() => setActive(null)}>
        <CartesianGrid vertical={false} stroke="var(--rule)" />
        <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: "var(--rule)" }} interval="preserveStartEnd" minTickGap={32} tickMargin={8} tick={<AxisTick />} />
        <YAxis domain={["auto", "auto"]} tickLine={false} axisLine={false} width={40} tick={tick} />
        {/* No floating tooltip: the readout under the strip shows the hour you point at. */}
        <Tooltip content={() => null} cursor={false} />
        {active != null && <ReferenceLine x={rows[active].label} stroke="var(--ink)" strokeWidth={1} />}
        {hasBand && <Area dataKey="band" stroke="none" fill="var(--color-band)" fillOpacity={0.15} isAnimationActive={false} />}
        <Line dataKey="persistence" stroke="var(--color-persistence)" strokeDasharray="5 4" strokeWidth={1.5} dot={false} activeDot={false} isAnimationActive={false} />
        <Line dataKey="forecast" stroke="var(--color-forecast)" strokeWidth={2.5} dot={dot} activeDot={{ r: 4, fill: "var(--ink)", stroke: "var(--paper)" }} isAnimationActive={false} />
      </ComposedChart>
    </ChartContainer>
  )
}

// Line samples for the legend: solid vs dashed, so the two lines differ by shape too.
export function LineKey({ dashed, color, children }: { dashed?: boolean; color: string; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg width="28" height="8" aria-hidden><line x1="0" y1="4" x2="28" y2="4" stroke={color} strokeWidth={dashed ? 1.5 : 2.5} strokeDasharray={dashed ? "5 4" : undefined} /></svg>
      {children}
    </span>
  )
}
