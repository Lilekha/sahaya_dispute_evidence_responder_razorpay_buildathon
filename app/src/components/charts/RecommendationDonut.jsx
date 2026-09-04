import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'
import { colors } from '../../lib/theme'

export default function RecommendationDonut({ contestCount, acceptCount }) {
  const total = contestCount + acceptCount
  const data = [
    { name: 'Contest', value: contestCount, color: colors.contest },
    { name: 'Accept', value: acceptCount, color: colors.accept },
  ].filter((d) => d.value > 0)

  return (
    <div className="relative h-[140px] w-[140px] shrink-0">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            innerRadius={46}
            outerRadius={68}
            startAngle={90}
            endAngle={-270}
            stroke="none"
            isAnimationActive={false}
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span className="num text-[24px] font-semibold text-ink">{total}</span>
        <span className="text-[11px] text-slate">disputes</span>
      </div>
    </div>
  )
}
