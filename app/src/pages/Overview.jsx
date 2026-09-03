import { useMemo } from 'react'
import { useData } from '../context/DataContext'
import { inr, pct } from '../lib/format'
import StatRow from '../components/StatRow'
import ReasonValueChart from '../components/charts/ReasonValueChart'
import DeadlineChart from '../components/charts/DeadlineChart'

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

  return (
    <div className="flex flex-col gap-6">
      <p className="text-[20px] leading-relaxed text-ink">
        SaHaYa recommends contesting <span className="num font-semibold">{m.n_contest}</span> of{' '}
        <span className="font-semibold">{m.name}</span>&rsquo;s{' '}
        <span className="num font-semibold">{m.n_disputes}</span> disputes, and accepting the
        other <span className="num font-semibold">{m.n_accept}</span>.
        <br />
        Contesting everything would waste{' '}
        <span className="num font-semibold">{inr(wastedFees)}</span> in fees on cases the
        evidence cannot win.
      </p>

      <StatRow
        items={[
          { label: 'Value at risk', value: inr(m.at_risk_value) },
          { label: 'Projected recovery', value: inr(m.projected_recovery) },
          { label: 'Disputes to review', value: String(m.n_disputes) },
          { label: 'Evidence completeness', value: pct(m.mean_packet_completeness) },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
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
