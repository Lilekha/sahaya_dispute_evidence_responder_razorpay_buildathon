import { AlertTriangle, Check, Minus } from 'lucide-react'
import ProbabilityBar from './ProbabilityBar'
import { formatDate, sentenceCase } from '../lib/format'
import { colors } from '../lib/theme'

const STATUS_ORDER = { SUBMIT: 0, GAP: 1, SKIP: 2 }

export default function EvidenceChecklist({ dispute }) {
  const sortedSlots = [...dispute.evidence_slots].sort(
    (a, b) => STATUS_ORDER[a.status] - STATUS_ORDER[b.status],
  )

  return (
    <div className="border border-line bg-surface p-4">
      <h2 className="text-base font-semibold text-ink">Evidence checklist</h2>
      <p className="mt-1 text-sm text-slate">
        The documents the card network requires for this claim type, and whether this merchant
        has them on file.
      </p>
      <p className="num mt-2 text-sm text-slate">
        {dispute.evidence_submitted} of {dispute.evidence_required} required documents available.
      </p>
      <ul className="mt-4 divide-y divide-line">
        {sortedSlots.map((slot) => (
          <li key={slot.evidence_type} className="flex items-center gap-3 py-2.5 text-sm">
            {slot.status === 'SUBMIT' && (
              <Check className="h-4 w-4 shrink-0 text-contest" aria-hidden="true" />
            )}
            {slot.status === 'GAP' && (
              <AlertTriangle className="h-4 w-4 shrink-0 text-gap" aria-hidden="true" />
            )}
            {slot.status === 'SKIP' && (
              <Minus className="h-4 w-4 shrink-0 text-slate" aria-hidden="true" />
            )}

            <span className={`flex-1 ${slot.status === 'SKIP' ? 'text-slate' : 'text-ink'}`}>
              {sentenceCase(slot.label)}
            </span>

            {slot.status === 'SUBMIT' && (
              <span className="flex items-center gap-3 text-[11px] text-slate">
                <span>{slot.source_system}</span>
                <span className="num">{formatDate(slot.evidence_timestamp)}</span>
                <ProbabilityBar value={slot.quality} width={48} color={colors.dodger} />
              </span>
            )}
            {slot.status === 'GAP' && (
              <span className="text-[13px] text-gap">Required but not on file</span>
            )}
            {slot.status === 'SKIP' && (
              <span className="text-[13px] text-slate">Not required for this claim type</span>
            )}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[12px] text-slate">
        Bar length shows document quality — how complete and legible the record is, not just
        whether it exists.
      </p>
    </div>
  )
}
