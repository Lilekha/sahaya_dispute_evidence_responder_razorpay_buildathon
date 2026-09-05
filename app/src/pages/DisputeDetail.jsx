import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useData } from '../context/DataContext'
import { inr, daysLeft, humanReason, formatDate } from '../lib/format'
import DecisionPanel from '../components/DecisionPanel'
import EvidenceChecklist from '../components/EvidenceChecklist'
import RebuttalPanel from '../components/RebuttalPanel'
import DriverList from '../components/DriverList'

const submissionDateFormatter = new Intl.DateTimeFormat('en-IN', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

export default function DisputeDetail() {
  const { id } = useParams()
  const { data, metrics } = useData()
  const [submission, setSubmission] = useState(null)
  const navigate = useNavigate()

  const dispute = data?.disputes.find((d) => d.dispute_id === id)

  useEffect(() => {
    setSubmission(null)
  }, [id])

  if (!dispute) {
    return (
      <div className="border border-line bg-surface p-8 text-center text-sm text-slate">
        No dispute found with ID {id}.{' '}
        <Link
          to="/disputes"
          className="text-dodger underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
        >
          Back to disputes
        </Link>
        .
      </div>
    )
  }

  const isContest = dispute.recommendation === 'CONTEST'
  const isUrgent = dispute.days_to_deadline <= 3
  const primaryLabel = isContest ? 'Approve and submit' : 'Approve and accept'
  const secondaryLabel = isContest ? 'Override to accept' : 'Override to contest'
  const rocAuc = metrics?.win_prediction?.test_roc_auc

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-5">
      <div className="flex flex-col gap-6 md:col-span-3">
        <div>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="mb-4 text-[13px] font-medium text-slate hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
          >
            ← Back to disputes
          </button>
          <div className="flex items-baseline gap-3">
            <h1 className="text-[20px] font-semibold text-ink">{dispute.dispute_id}</h1>
            <span className="text-sm text-slate">{humanReason(dispute.reason_code)}</span>
          </div>
          <div className="num mt-1 text-[28px] font-semibold text-ink">
            {inr(dispute.dispute_amount)}
          </div>
          <div className="mt-1 flex items-center gap-2 text-sm text-slate">
            <span>{dispute.network}</span>
            <span aria-hidden="true">·</span>
            <span className={isUrgent ? 'text-gap' : ''}>
              {daysLeft(dispute.days_to_deadline)} to respond
            </span>
          </div>
        </div>

        <DecisionPanel dispute={dispute} />
        <EvidenceChecklist dispute={dispute} />
        {isContest && <RebuttalPanel text={dispute.rebuttal_draft} />}

        {submission ? (
          <div className="border border-line bg-canvas p-3 text-sm text-ink">
            Submitted for review by you on {submissionDateFormatter.format(submission.date)}.
          </div>
        ) : (
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setSubmission({ action: 'approve', date: new Date() })}
              className="bg-dodger px-4 py-2 text-sm font-medium text-white hover:bg-dodger/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger focus-visible:ring-offset-2"
            >
              {primaryLabel}
            </button>
            <button
              type="button"
              onClick={() => setSubmission({ action: 'override', date: new Date() })}
              className="border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-canvas focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
            >
              {secondaryLabel}
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-6 md:col-span-2">
        <DriverList drivers={dispute.top_drivers} />

        <div className="border border-line bg-surface p-4">
          <h2 className="text-base font-semibold text-ink">Case facts</h2>
          <dl className="mt-4 flex flex-col gap-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Customer</dt>
              <dd className="text-ink">{dispute.customer_name ?? '—'}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">City</dt>
              <dd className="text-ink">{dispute.customer_city ?? '—'}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Prior orders</dt>
              <dd className="num text-ink">{dispute.customer_previous_orders ?? '—'}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Prior disputes</dt>
              <dd className="num text-ink">{dispute.customer_previous_disputes ?? '—'}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Transaction ID</dt>
              <dd className="num text-ink">{dispute.transaction_id}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Network</dt>
              <dd className="text-ink">{dispute.network}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Dispute raised</dt>
              <dd className="num text-ink">{formatDate(dispute.dispute_created_at)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Respond by</dt>
              <dd className="num text-ink">{formatDate(dispute.respond_by)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate">Historical action</dt>
              <dd className="text-ink">
                {dispute.historical_action.charAt(0).toUpperCase() +
                  dispute.historical_action.slice(1)}
              </dd>
            </div>
          </dl>
        </div>

        <p className="text-sm text-slate">
          Win probability from a calibrated random forest
          {rocAuc != null ? ` (test ROC-AUC ${rocAuc.toFixed(2)})` : ''}. Evidence requirements
          from the card network&rsquo;s published rules for this reason code.
        </p>
      </div>
    </div>
  )
}
