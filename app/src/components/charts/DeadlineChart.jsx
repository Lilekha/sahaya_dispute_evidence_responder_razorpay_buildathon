import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { colors } from '../../lib/theme'

const BUCKETS = [
  { label: '≤3 days', test: (n) => n <= 3 },
  { label: '4–7 days', test: (n) => n > 3 && n <= 7 },
  { label: '8–14 days', test: (n) => n > 7 && n <= 14 },
  { label: '15+ days', test: (n) => n > 14 },
]

export default function DeadlineChart({ disputes }) {
  const data = BUCKETS.map((bucket) => ({
    label: bucket.label,
    count: disputes.filter((d) => bucket.test(d.days_to_deadline)).length,
  }))

  return (
    <ResponsiveContainer width="100%" height={180} className="num">
      <BarChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12, fill: colors.ink }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          width={32}
          tick={{ fontSize: 11, fill: colors.slate }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <Tooltip
          formatter={(value) => [`${value} disputes`, undefined]}
          contentStyle={{ borderRadius: 4, borderColor: colors.line, fontSize: 12 }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} barSize={48} isAnimationActive={false}>
          {data.map((entry, index) => (
            <Cell key={entry.label} fill={index === 0 ? colors.gap : colors.dodger} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
