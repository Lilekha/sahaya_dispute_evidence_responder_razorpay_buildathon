import { ArrowDown, ArrowUp } from 'lucide-react'
import { humanReason } from '../lib/format'
import { colors } from '../lib/theme'

function humanizeFeature(feature) {
  const match = feature.match(/^Claim type: (.+)$/)
  if (match) {
    return `Claim type: ${humanReason(match[1].replace(/ /g, '_'))}`
  }
  return feature
}

export default function DriverList({ drivers }) {
  const maxImpact = Math.max(...drivers.map((d) => Math.abs(d.impact)), 0.0001)

  return (
    <div className="border border-line bg-surface p-4">
      <h2 className="text-base font-semibold text-ink">What moved this prediction</h2>
      <ul className="mt-4 flex flex-col gap-3">
        {drivers.map((driver) => {
          const raises = driver.direction === 'raises'
          const widthPct = (Math.abs(driver.impact) / maxImpact) * 100
          return (
            <li key={driver.feature} className="flex items-center gap-3 text-sm">
              {raises ? (
                <ArrowUp className="h-4 w-4 shrink-0 text-contest" aria-hidden="true" />
              ) : (
                <ArrowDown className="h-4 w-4 shrink-0 text-gap" aria-hidden="true" />
              )}
              <span className="w-44 shrink-0 text-ink">{humanizeFeature(driver.feature)}</span>
              <span className="h-1.5 flex-1 overflow-hidden rounded border border-line bg-canvas">
                <span
                  className="block h-full"
                  style={{
                    width: `${widthPct}%`,
                    backgroundColor: raises ? colors.contest : colors.gap,
                  }}
                />
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
