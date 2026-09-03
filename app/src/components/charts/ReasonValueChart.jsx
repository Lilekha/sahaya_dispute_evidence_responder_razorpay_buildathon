import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { inr, humanReason } from '../../lib/format'
import { colors } from '../../lib/theme'

export default function ReasonValueChart({ disputes }) {
  const totals = {}
  for (const d of disputes) {
    totals[d.reason_code] = (totals[d.reason_code] ?? 0) + d.dispute_amount
  }
  const data = Object.entries(totals)
    .map(([reason_code, value]) => ({ reason_code, label: humanReason(reason_code), value }))
    .sort((a, b) => b.value - a.value)

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
        <XAxis
          type="number"
          tickFormatter={(v) => inr(v)}
          tick={{ fontSize: 11, fill: colors.slate }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={150}
          tick={{ fontSize: 12, fill: colors.ink }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <Tooltip
          formatter={(value) => inr(value)}
          contentStyle={{ borderRadius: 4, borderColor: colors.line, fontSize: 12 }}
        />
        <Bar dataKey="value" fill={colors.dodger} radius={[0, 4, 4, 0]} barSize={16} />
      </BarChart>
    </ResponsiveContainer>
  )
}
