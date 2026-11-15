"use client"

import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts"

import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { FailureDay } from "@/lib/api"

const config = {
  true: { label: "What really happened", color: "oklch(0.3 0 0)" },
  model: { label: "GridGreen forecast", color: "oklch(0.55 0.14 160)" },
  persistence: { label: "Persistence", color: "oklch(0.65 0 0)" },
} satisfies ChartConfig

// Failure days are UTC calendar days (as in results/failures.md), so the axis is in UTC.
export function FailureChart({ day }: { day: FailureDay }) {
  const rows = day.hours.map((h) => ({ ...h, label: `${h.ts_utc.slice(11, 13)}:00` }))
  return (
    <ChartContainer config={config} className="aspect-auto h-[240px] w-full">
      <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 4, left: 4 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="label" tickLine={false} interval="preserveStartEnd" minTickGap={28} tickMargin={8} fontSize={11} />
        <YAxis domain={["auto", "auto"]} tickLine={false} width={44} fontSize={11} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line dataKey="true" stroke="var(--color-true)" strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line dataKey="model" stroke="var(--color-model)" strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line dataKey="persistence" stroke="var(--color-persistence)" strokeDasharray="5 4" dot={false} isAnimationActive={false} />
        <ChartLegend content={<ChartLegendContent />} />
      </LineChart>
    </ChartContainer>
  )
}
