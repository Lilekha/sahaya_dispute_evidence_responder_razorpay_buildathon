import { colors } from '../lib/theme'

export default function ProbabilityBar({ value, width = 40, color = colors.dodger }) {
  const widthPct = Math.round(Math.max(0, Math.min(1, value ?? 0)) * 100)
  return (
    <span
      className="inline-block h-1.5 shrink-0 overflow-hidden rounded border border-line bg-canvas align-middle"
      style={{ width }}
    >
      <span className="block h-full" style={{ width: `${widthPct}%`, backgroundColor: color }} />
    </span>
  )
}
