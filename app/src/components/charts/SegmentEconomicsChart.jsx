import {
  Bar,
  BarChart,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { inr } from '../../lib/format'
import { colors } from '../../lib/theme'

const WARNING_RED = '#C62828'

function ContestLabel({ x, y, width, height, value }) {
  const isNegative = value < 0
  const labelY = isNegative ? y + height + 13 : y - 6
  return (
    <text
      x={x + width / 2}
      y={labelY}
      textAnchor="middle"
      fontSize={10}
      className="num"
      fill={isNegative ? WARNING_RED : colors.ink}
    >
      {inr(value)}
    </text>
  )
}

export default function SegmentEconomicsChart({ segments }) {
  const data = segments.map((s) => ({
    segment: s.segment,
    alwaysContest: s.always_contest,
    model: s.model,
  }))

  return (
    <ResponsiveContainer width="100%" height={200} className="num">
      <BarChart data={data} margin={{ top: 16, right: 8, bottom: 4, left: 8 }}>
        <XAxis
          dataKey="segment"
          tickFormatter={(v) => v.replace(/ \(.*\)/, '')}
          tick={{ fontSize: 11, fill: colors.ink }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v) => inr(v)}
          tick={{ fontSize: 10, fill: colors.slate }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
          width={64}
        />
        <ReferenceLine y={0} stroke={colors.line} />
        <Tooltip
          formatter={(value) => inr(value)}
          contentStyle={{ borderRadius: 4, borderColor: colors.line, fontSize: 12 }}
        />
        <Bar
          dataKey="alwaysContest"
          name="Always contest"
          fill={colors.slate}
          radius={[4, 4, 0, 0]}
          barSize={18}
          isAnimationActive={false}
        >
          <LabelList dataKey="alwaysContest" content={ContestLabel} />
        </Bar>
        <Bar
          dataKey="model"
          name="SaHaYa"
          fill={colors.dodger}
          radius={[4, 4, 0, 0]}
          barSize={18}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
