import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { pct, sentenceCase } from '../../lib/format'
import { colors } from '../../lib/theme'

export default function EvidenceGapChart({ disputes }) {
  const evidenceTypes = disputes[0]
    ? disputes[0].evidence_slots.map((s) => ({ type: s.evidence_type, label: sentenceCase(s.label) }))
    : []

  const data = evidenceTypes
    .map(({ type, label }) => {
      const gapCount = disputes.filter(
        (d) => d.evidence_slots.find((s) => s.evidence_type === type)?.status === 'GAP',
      ).length
      return { label, share: disputes.length ? gapCount / disputes.length : 0 }
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
        <Tooltip
          formatter={(value) => pct(value, 0)}
          contentStyle={{ borderRadius: 4, borderColor: colors.line, fontSize: 12 }}
        />
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
