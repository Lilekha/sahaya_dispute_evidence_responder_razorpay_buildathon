const wholeRupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

const fractionalRupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function inr(v) {
  if (v == null || Number.isNaN(v)) return '—'
  const formatter = Math.abs(v) < 100 ? fractionalRupees : wholeRupees
  return formatter.format(v).replace('-', '−')
}

export function pct(v, d = 1) {
  if (v == null || Number.isNaN(v)) return '—'
  return `${(v * 100).toFixed(d)}%`
}

const REASON_LABELS = {
  MERCHANDISE_NOT_RECEIVED: 'Goods not received',
  UNAUTHORIZED_TRANSACTION: 'Unauthorised transaction',
  MERCHANDISE_NOT_AS_DESCRIBED: 'Not as described',
  CREDIT_NOT_PROCESSED: 'Refund not processed',
  RECURRING_BILLING_DISPUTE: 'Subscription charge disputed',
  DUPLICATE_TRANSACTION: 'Charged twice',
}

export function humanReason(code) {
  return REASON_LABELS[code] ?? code
}

const dateFormatter = new Intl.DateTimeFormat('en-IN', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

// dispute_created_at/respond_by/evidence_timestamp are "YYYY-MM-DD HH:MM:SS",
// not standard ISO 8601 — parsed manually since engines vary on that format.
export function formatDate(dateTimeStr) {
  if (!dateTimeStr) return '—'
  const [datePart] = dateTimeStr.split(' ')
  const [year, month, day] = datePart.split('-').map(Number)
  return dateFormatter.format(new Date(year, month - 1, day))
}

export function daysLeft(days) {
  if (days == null || Number.isNaN(days)) return '—'
  if (days < 0) {
    const n = Math.abs(days)
    return `${n} day${n === 1 ? '' : 's'} overdue`
  }
  return `${days} day${days === 1 ? '' : 's'}`
}
