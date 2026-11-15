"use client"

import { Area, CartesianGrid, ComposedChart, Line, XAxis, YAxis } from "recharts"

import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import { dayLabel, hourLabel, type Forecast } from "@/lib/api"

const config = {
  forecast: { label: "GridGreen forecast", color: "oklch(0.55 0.14 160)" },
  persistence: { label: "Persistence (tomorrow = today)", color: "oklch(0.65 0 0)" },
  band: { label: "10–90 % range", color: "oklch(0.55 0.14 160)" },
} satisfies ChartConfig

type DotProps = { cx?: number; cy?: number; index?: number }

export function ForecastChart({ data }: { data: Forecast }) {
  const rows = data.hours.map((h) => ({
    label: `${dayLabel(h.ts_local)} ${hourLabel(h.ts_local)}`,
    forecast: h.forecast,
    persistence: h.persistence,
    band: h.lo != null && h.hi != null ? [h.lo, h.hi] : null,
  }))
  const hasBand = rows.some((r) => r.band)
  // Rank (1 = cleanest) for each of the 3 cleanest hours, keyed by hour index.
  const rank = new Map(data.cleanest_hours.map((ts, i) => [data.hours.findIndex((h) => h.ts_local === ts), i + 1]))

  // Cleanest hours get a diamond plus a "1/2/3" rank label, so colour is never the only cue.
  const dot = ({ cx, cy, index }: DotProps) => {
    const r = index != null ? rank.get(index) : undefined
    if (r == null || cx == null || cy == null) return <g key={index} />
    return (
      <g key={index}>
        <path d={`M${cx},${cy - 7}L${cx + 7},${cy}L${cx},${cy + 7}L${cx - 7},${cy}Z`} fill="var(--color-forecast)" stroke="white" strokeWidth={1.5} />
        <text x={cx} y={cy + 22} textAnchor="middle" fontSize={11} fontWeight={600} fill="currentColor">
          {r}
        </text>
      </g>
    )
  }

  return (
    <ChartContainer config={config} className="aspect-auto h-[320px] w-full">
      <ComposedChart data={rows} margin={{ top: 10, right: 12, bottom: 4, left: 4 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="label" tickLine={false} interval="preserveStartEnd" minTickGap={28} tickMargin={8} fontSize={11} />
        <YAxis domain={["auto", "auto"]} tickLine={false} width={44} fontSize={11} unit="" label={{ value: "gCO₂/kWh", angle: -90, position: "insideLeft", fontSize: 11 }} />
        <ChartTooltip content={<ChartTooltipContent />} />
        {hasBand && <Area dataKey="band" stroke="none" fill="var(--color-band)" fillOpacity={0.15} isAnimationActive={false} />}
        <Line dataKey="persistence" stroke="var(--color-persistence)" strokeDasharray="5 4" strokeWidth={1.5} dot={false} isAnimationActive={false} />
        <Line dataKey="forecast" stroke="var(--color-forecast)" strokeWidth={2.5} dot={dot} isAnimationActive={false} />
        <ChartLegend content={<ChartLegendContent />} />
      </ComposedChart>
    </ChartContainer>
  )
}
