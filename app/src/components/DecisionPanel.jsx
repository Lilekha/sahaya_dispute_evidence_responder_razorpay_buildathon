import ProbabilityBar from './ProbabilityBar'
import RecommendationBadge from './RecommendationBadge'
import { inr, pct } from '../lib/format'
import { colors } from '../lib/theme'

export default function DecisionPanel({ dispute }) {
  const { p_win, breakeven, dispute_amount, contest_fee, expected_value, recommendation } = dispute
  const isContest = recommendation === 'CONTEST'

  return (
    <div className="border border-line bg-surface p-4">
      <h2 className="text-base font-semibold text-ink">Decision</h2>

      <div className="mt-4 flex flex-col gap-3">
        <div className="flex items-center gap-4">
          <span className="w-44 shrink-0 text-sm text-slate">Win probability</span>
          <span className="num w-14 shrink-0 text-sm text-ink">{pct(p_win)}</span>
          <ProbabilityBar value={p_win} width={200} color={colors.dodger} />
        </div>
        <div className="flex items-center gap-4">
          <span className="w-44 shrink-0 text-sm text-slate">Break-even threshold</span>
          <span className="num w-14 shrink-0 text-sm text-ink">{pct(breakeven)}</span>
          <ProbabilityBar value={breakeven} width={200} color={colors.slate} />
        </div>
      </div>

      <div className="num mt-6 flex flex-wrap items-baseline gap-2 border-y border-line py-4 text-base text-ink">
        <span>{p_win.toFixed(3)}</span>
        <span className="text-slate">×</span>
        <span>{inr(dispute_amount)}</span>
        <span className="text-slate">−</span>
        <span>{inr(contest_fee)}</span>
        <span className="text-slate">=</span>
        <span className="font-semibold">{inr(expected_value)}</span>
        <span className="text-sm font-normal text-slate">expected value</span>
      </div>

      <div className="mt-4 flex items-center gap-2">
        <span className="text-sm text-slate">Recommendation</span>
        <RecommendationBadge recommendation={recommendation} />
      </div>

      <p className="mt-3 text-sm text-ink">
        {isContest
          ? `Worth contesting — the expected recovery exceeds the ${inr(contest_fee)} cost of filing.`
          : `Not worth contesting — the ${inr(contest_fee)} filing cost exceeds what we expect to recover.`}
      </p>
    </div>
  )
}
