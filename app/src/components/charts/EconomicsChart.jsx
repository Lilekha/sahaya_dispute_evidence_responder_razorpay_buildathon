import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { inr } from '../../lib/format'
import { colors } from '../../lib/theme'

export default function EconomicsChart({ economics }) {
  const data = [
    { label: 'Always accept', value: economics.always_accept },
    { label: 'Always contest', value: economics.always_contest },
    { label: 'SaHaYa', value: economics.model },
    { label: 'Perfect foresight', value: economics.perfect_foresight },
  ]

  return (
    <ResponsiveContainer width="100%" height={200} className="num">
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
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
          width={110}
          tick={{ fontSize: 12, fill: colors.ink }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <Tooltip
          formatter={(value) => inr(value)}
          contentStyle={{ borderRadius: 4, borderColor: colors.line, fontSize: 12 }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20} isAnimationActive={false}>
          {data.map((entry) => (
            <Cell key={entry.label} fill={entry.label === 'SaHaYa' ? colors.dodger : colors.slate} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
