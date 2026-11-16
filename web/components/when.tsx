// An hour like "Sat 11 AM": digits in Plex Mono (tabular), words in the surrounding face.
// Plex Mono's wide space would otherwise open a gap between "11" and "AM".
import { dayLabel, hourLabel } from "@/lib/api"

export function When({ iso, day = false }: { iso: string; day?: boolean }) {
  const [n, ampm] = hourLabel(iso).split(" ")
  return (
    <span className="whitespace-nowrap">
      {day && `${dayLabel(iso)} `}
      <span className="num">{n}</span>&#8239;{ampm}
    </span>
  )
}

// Same idea for SVG axis labels ("Sat 3 AM"): numbers get the mono face, words the text face.
export function AxisTick({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) {
  const parts = (payload?.value ?? "").split(/(\d+)/)
  return (
    <text x={x} y={(y ?? 0) + 12} textAnchor="middle" fontSize={12} fill="var(--ink-2)">
      {parts.map((p, i) => <tspan key={i} fontFamily={/\d/.test(p) ? "var(--font-plex-mono)" : "var(--font-plex-sans)"}>{p}</tspan>)}
    </text>
  )
}
