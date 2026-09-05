import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { pct, sentenceCase } from '../../lib/format'
import { colors } from '../../lib/theme'

function GapTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const { label, count, total, share } = payload[0].payload
  return (
    <div className="border border-line bg-surface px-2.5 py-1.5 text-[12px]">
      <div className="font-medium text-ink">{label}</div>
      <div className="text-slate">
        {count} of {total} disputes · {pct(share, 0)}
      </div>
    </div>
  )
}

export default function EvidenceGapChart({ disputes }) {
  const evidenceTypes = disputes[0]
    ? disputes[0].evidence_slots.map((s) => ({ type: s.evidence_type, label: sentenceCase(s.label) }))
    : []

  const data = evidenceTypes
    .map(({ type, label }) => {
      const gapCount = disputes.filter(
        (d) => d.evidence_slots.find((s) => s.evidence_type === type)?.status === 'GAP',
      ).length
      return {
        label,
        count: gapCount,
        total: disputes.length,
        share: disputes.length ? gapCount / disputes.length : 0,
      }
    })
    .sort((a, b) => b.share - a.share)

  return (
    <ResponsiveContainer width="100%" height={220} className="num">
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
        <XAxis
          type="number"
          domain={[0, 1]}
          tickFormatter={(v) => pct(v, 0)}
          tick={{ fontSize: 11, fill: colors.slate }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={160}
          tick={{ fontSize: 12, fill: colors.ink }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <Tooltip content={<GapTooltip />} cursor={{ fill: colors.canvas }} />
        <Bar
          dataKey="share"
          fill={colors.gap}
          radius={[0, 4, 4, 0]}
          barSize={16}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
