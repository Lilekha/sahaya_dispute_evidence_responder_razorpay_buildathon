import { useData } from '../context/DataContext'
import { inr } from '../lib/format'
import EconomicsChart from '../components/charts/EconomicsChart'

export default function Methodology() {
  const { metrics } = useData()

  if (!metrics) return null

  const { win_prediction, evidence_selection, economics, uplift_vs_always_contest } = metrics

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="border border-line bg-surface p-4">
          <h2 className="text-base font-semibold text-ink">Evidence selection</h2>
          <dl className="mt-4 flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate">Precision</dt>
              <dd className="num text-ink">{evidence_selection.precision.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate">Recall</dt>
              <dd className="num text-ink">{evidence_selection.recall.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate">Exact match</dt>
              <dd className="num text-ink">{evidence_selection.exact_match_rate.toFixed(3)}</dd>
            </div>
          </dl>
          <p className="mt-3 text-sm italic text-slate">
            Implements the card networks&rsquo; published requirement rules — a deterministic
            standard, so near-perfect accuracy is the expected result.
          </p>
        </div>

        <div className="border border-line bg-surface p-4">
          <h2 className="text-base font-semibold text-ink">Win prediction</h2>
          <dl className="mt-4 flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate">ROC-AUC</dt>
              <dd className="num text-ink">{win_prediction.test_roc_auc.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate">Precision</dt>
              <dd className="num text-ink">{win_prediction.precision.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate">Recall</dt>
              <dd className="num text-ink">{win_prediction.recall.toFixed(3)}</dd>
            </div>
          </dl>
          <p className="mt-3 text-sm italic text-slate">
            Predicts a bank&rsquo;s judgement, which is genuinely uncertain. Reported as measured.
          </p>
        </div>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">The money view</h2>
        <div className="mt-4">
          <EconomicsChart economics={economics} />
        </div>
        <p className="mt-3 text-sm text-ink">
          SaHaYa recovers <span className="num font-semibold">{inr(uplift_vs_always_contest)}</span>{' '}
          more than contesting every dispute.
        </p>
        <p className="mt-2 text-sm text-slate">
          Contest fees are small relative to most dispute amounts, so contesting everything is a
          strong baseline. SaHaYa&rsquo;s advantage concentrates in small-value disputes, where the
          filing fee approaches the amount at stake and contesting destroys money.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="border border-line bg-surface p-4">
          <div className="text-[11px] text-slate">Cost of contesting a losing case</div>
          <div className="num mt-1 text-[28px] font-semibold text-ink">
            {inr(metrics.false_positive_cost)}
          </div>
          <p className="mt-2 text-sm text-slate">
            Fees spent contesting disputes that go on to lose, with nothing recovered.
          </p>
        </div>

        <div className="border border-line bg-surface p-4">
          <div className="text-[11px] text-slate">Cost of accepting a winnable case</div>
          <div className="num mt-1 text-[28px] font-semibold text-ink">
            {inr(metrics.false_negative_cost)}
          </div>
          <p className="mt-2 text-sm text-slate">
            Recoverable value forgone by accepting disputes the evidence could have won.
          </p>
        </div>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">Scope and limits</h2>
        <ul className="mt-4 flex flex-col gap-3 text-sm text-ink">
          <li>
            <span className="font-semibold">Card disputes only.</span> NPCI auto-resolves UPI
            chargebacks through settlement reconciliation — no evidence is submitted and the
            merchant makes no decision, so an evidence responder has nothing to do there.
          </li>
          <li>
            <span className="font-semibold">Synthetic data.</span> Calibrated to published
            industry benchmarks; no India-specific chargeback statistics are public. Outcomes are
            modelled, not observed.
          </li>
          <li>
            <span className="font-semibold">Defense only.</span> Evidence is never generated.
            Gaps are disclosed. Every recommendation requires human sign-off.
          </li>
          <li>
            <span className="font-semibold">Merchant-scoped.</span> A customer disputing across
            several merchants appears as unrelated identities, matching a real single-merchant
            integration.
          </li>
        </ul>
      </div>
    </div>
  )
}
