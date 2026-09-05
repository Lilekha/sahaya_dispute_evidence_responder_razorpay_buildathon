import { useMemo } from 'react'
import { useData } from '../context/DataContext'
import { inr, pct } from '../lib/format'
import StatRow from '../components/StatRow'
import ReasonValueChart from '../components/charts/ReasonValueChart'
import DeadlineChart from '../components/charts/DeadlineChart'
import RecommendationDonut from '../components/charts/RecommendationDonut'

export default function Overview() {
  const { selectedMerchant, merchantDisputes } = useData()

  const wastedFees = useMemo(
    () =>
      merchantDisputes
        .filter((d) => d.recommendation === 'ACCEPT')
        .reduce((sum, d) => sum + d.contest_fee, 0),
    [merchantDisputes],
  )

  if (!selectedMerchant) return null

  const m = selectedMerchant
  const contestShare = m.n_disputes ? (m.n_contest / m.n_disputes) * 100 : 0
  const acceptShare = 100 - contestShare

  const heroLine1 =
    m.n_contest > 0
      ? `${m.n_contest} of ${m.n_disputes} worth contesting`
      : `None of these ${m.n_disputes} are worth contesting`
  const heroLine2 =
    m.n_contest > 0
      ? `Accepting the other ${m.n_accept} avoids ${inr(wastedFees)} in filing fees on cases the evidence cannot win.`
      : `Contesting them would cost ${inr(wastedFees)} more than accepting.`

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-stretch border border-line bg-surface">
        <div className="flex w-[180px] shrink-0 items-center justify-center border-r border-line p-4">
          <RecommendationDonut contestCount={m.n_contest} acceptCount={m.n_accept} />
        </div>
        <div className="flex flex-1 flex-col justify-center gap-1 p-4">
          <p className="num text-[20px] font-semibold text-ink">{heroLine1}</p>
          <p className="text-sm text-slate">{heroLine2}</p>
        </div>
      </div>

      <StatRow
        items={[
          { label: 'Total disputed', value: inr(m.total_disputed) },
          {
            label: 'Projected recovery',
            value: inr(m.projected_recovery),
            note: m.projected_recovery === 0 ? 'No disputes meet the threshold to contest' : null,
          },
          { label: 'Disputes to review', value: String(m.n_disputes) },
          { label: 'Evidence completeness', value: pct(m.mean_packet_completeness) },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="border border-line bg-surface p-4">
          <h2 className="text-base font-semibold text-ink">Recommendation split</h2>
          <div className="mt-4 flex h-3 w-full overflow-hidden rounded border border-line">
            <div className="bg-contest" style={{ width: `${contestShare}%` }} />
            <div className="bg-accept" style={{ width: `${acceptShare}%` }} />
          </div>
          <div className="mt-2 flex items-center gap-4 text-[13px] text-slate">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-contest" aria-hidden="true" />
              <span className="num">{m.n_contest}</span> contest
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-accept" aria-hidden="true" />
              <span className="num">{m.n_accept}</span> accept
            </span>
          </div>
          <p className="mt-4 text-sm text-slate">
            <span className="num">{m.n_accept}</span> disputes fall below their break-even
            threshold. Contesting them costs more than the amount at stake.
          </p>
        </div>

        <div className="border border-line bg-surface p-4">
          <h2 className="text-base font-semibold text-ink">Where the money sits</h2>
          <div className="mt-4">
            <ReasonValueChart disputes={merchantDisputes} />
          </div>
        </div>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">Deadline pressure</h2>
        <div className="mt-4">
          <DeadlineChart disputes={merchantDisputes} />
        </div>
      </div>
    </div>
  )
}
