import ProbabilityBar from './ProbabilityBar'
import RecommendationBadge from './RecommendationBadge'
import { inr, pct } from '../lib/format'
import { colors } from '../lib/theme'

export default function DecisionPanel({ dispute }) {
  const { p_win, breakeven, dispute_amount, contest_fee, expected_value, recommendation } = dispute
  const isContest = recommendation === 'CONTEST'
  const winOutcome = dispute_amount - contest_fee
  const loseOutcome = -contest_fee

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

      <div className="num mt-6 flex flex-col gap-2 border-y border-line py-4 text-sm text-ink">
        <div className="flex items-center justify-between gap-4">
          <span>
            If we contest and <span className="font-medium">win</span>{' '}
            <span className="text-slate">({pct(p_win)} likely)</span>
          </span>
          <span className="text-contest">+{inr(winOutcome)}</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span>
            If we contest and <span className="font-medium">lose</span>{' '}
            <span className="text-slate">({pct(1 - p_win)} likely)</span>
          </span>
          <span className="text-gap">{inr(loseOutcome)}</span>
        </div>
        <div className="mt-1 flex items-center justify-between gap-4 border-t border-line pt-2 font-semibold">
          <span className="text-sm font-normal text-slate">Expected value</span>
          <span>{inr(expected_value)}</span>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2">
        <span className="text-sm text-slate">Recommendation</span>
        <RecommendationBadge recommendation={recommendation} />
      </div>

      <p className="mt-3 text-sm text-ink">
        We need a {pct(breakeven)} chance of winning to justify the {inr(contest_fee)} filing
        cost. We estimate {pct(p_win)}, so contesting would{' '}
        {isContest ? 'recover money on average.' : 'lose money on average.'}
      </p>

      <p className="mt-3 text-[11px] text-slate">
        Expected value is the average across many similar disputes, not what you receive on this
        one.
      </p>
    </div>
  )
}
