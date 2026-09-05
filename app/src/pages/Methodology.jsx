import { useData } from '../context/DataContext'
import { inr } from '../lib/format'
import EconomicsChart from '../components/charts/EconomicsChart'
import SegmentEconomicsChart from '../components/charts/SegmentEconomicsChart'
import InfoTooltip from '../components/InfoTooltip'
import { colors } from '../lib/theme'

export default function Methodology() {
  const { metrics } = useData()

  if (!metrics) return null

  const { win_prediction, evidence_selection, economics, economics_by_segment } = metrics

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
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
          <div className="flex items-center gap-1.5">
            <h2 className="text-base font-semibold text-ink">Win prediction</h2>
            <InfoTooltip text="A calibrated Random Forest trained on past contested disputes. ROC-AUC measures how well it separates wins from losses (0.5 is random, 1.0 is perfect). Precision is the share of disputes it recommends contesting that actually win. Recall is the share of winnable disputes it catches." />
          </div>
          <dl className="mt-4 flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate">ROC-AUC</dt>
              <dd className="num text-ink">{win_prediction.test_roc_auc.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate">Precision (economic threshold)</dt>
              <dd className="num text-ink">{win_prediction.precision.toFixed(3)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate">Recall (economic threshold)</dt>
              <dd className="num text-ink">{win_prediction.recall.toFixed(3)}</dd>
            </div>
          </dl>

          <div className="mt-3 border-t border-line pt-3">
            <p className="text-[11px] text-slate">At the standard 0.5 threshold</p>
            <dl className="mt-2 flex flex-col gap-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate">Precision</dt>
                <dd className="num text-ink">{win_prediction.precision_at_half.toFixed(3)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate">Recall</dt>
                <dd className="num text-ink">{win_prediction.recall_at_half.toFixed(3)}</dd>
              </div>
            </dl>
          </div>

          <p className="mt-3 text-sm italic text-slate">
            SaHaYa contests some low-probability, high-value disputes because the payoff
            justifies the risk — which is why economic-threshold precision reads lower than
            standard precision. Both describe the same model; they answer different questions.
            Treat the exact decimal as approximate — the test set is a few hundred disputes.
          </p>
        </div>
      </div>

      <p className="text-[12px] text-slate">
        These model metrics are shown for evaluation purposes. A live merchant-facing product
        would not display them.
      </p>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">The money view</h2>
        <div className="mt-4 flex flex-col gap-6 md:flex-row">
          <div className="md:w-[45%]">
            <EconomicsChart economics={economics} />
          </div>
          <div className="md:flex-1">
            <h3 className="text-sm font-semibold text-ink">Where the judgement actually pays off</h3>
            <p className="mt-0.5 text-[13px] text-slate">
              Same two strategies, broken down by dispute size.
            </p>
            <div className="mt-3">
              <SegmentEconomicsChart segments={economics_by_segment} />
            </div>
            <div className="mt-2 flex items-center gap-4 text-[13px] text-slate">
              <span className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: colors.slate }}
                  aria-hidden="true"
                />
                Always contest
              </span>
              <span className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: colors.dodger }}
                  aria-hidden="true"
                />
                SaHaYa
              </span>
            </div>
          </div>
        </div>
        <p className="mt-6 text-sm text-ink">
          Overall, SaHaYa and blind contesting perform similarly — most disputes are worth
          fighting regardless, so blindly contesting everything is already a strong baseline. The
          difference concentrates in small disputes: fighting a ₹500 claim to recover ₹500 when
          the filing fee is ₹450 is mathematically hopeless, and blind contesting loses money on
          every one of those cases. SaHaYa correctly declines them.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
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
