"use client"

import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import { LineKey } from "@/components/forecast-chart"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { FailureDay } from "@/lib/api"

const config = {
  true: { label: "What really happened", color: "var(--ink)" },
  model: { label: "Our forecast", color: "var(--clean)" },
  persistence: { label: "Tomorrow = today", color: "var(--ink-2)" },
} satisfies ChartConfig

const tick = { fontFamily: "var(--font-plex-mono)", fontSize: "0.75rem", fill: "var(--ink-2)" }

// Failure days are UTC calendar days (as in results/failures.md), so the axis is in UTC.
export function FailureChart({ day }: { day: FailureDay }) {
  const rows = day.hours.map((h) => ({ ...h, label: `${h.ts_utc.slice(11, 13)}:00` }))
  return (
    <figure className="space-y-2">
      <figcaption className="flex flex-wrap gap-x-5 gap-y-1 text-step--1 text-ink-2">
        <LineKey color="var(--ink)">What really happened</LineKey>
        <LineKey color="var(--clean)">Our forecast</LineKey>
        <LineKey color="var(--ink-2)" dashed>Tomorrow = today</LineKey>
        <span>Hours in UTC</span>
      </figcaption>
      <ChartContainer config={config} className="aspect-auto h-[15rem] w-full">
        <LineChart data={rows} margin={{ top: 8, right: 28, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--rule)" />
          <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: "var(--rule)" }} interval="preserveStartEnd" minTickGap={32} tickMargin={8} tick={tick} />
          <YAxis domain={["auto", "auto"]} tickLine={false} axisLine={false} width={40} tick={tick} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line dataKey="true" stroke="var(--color-true)" strokeWidth={2.5} dot={false} isAnimationActive={false} />
          <Line dataKey="model" stroke="var(--color-model)" strokeWidth={2} dot={false} isAnimationActive={false} />
          <Line dataKey="persistence" stroke="var(--color-persistence)" strokeDasharray="5 4" strokeWidth={1.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ChartContainer>
    </figure>
  )
}
