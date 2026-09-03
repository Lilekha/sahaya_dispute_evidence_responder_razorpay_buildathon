import { useMemo } from 'react'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useData } from '../context/DataContext'
import { humanReason, sentenceCase } from '../lib/format'
import { colors } from '../lib/theme'
import EvidenceGapChart from '../components/charts/EvidenceGapChart'

const COMPLETENESS_BUCKET_LABELS = ['0–20%', '20–40%', '40–60%', '60–80%', '80–100%']

function CompletenessHistogram({ disputes }) {
  const buckets = [0, 0, 0, 0, 0]
  for (const d of disputes) {
    const idx = Math.min(4, Math.floor(d.packet_completeness * 5))
    buckets[idx] += 1
  }
  const data = COMPLETENESS_BUCKET_LABELS.map((label, i) => ({ label, count: buckets[i] }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12, fill: colors.ink }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          width={32}
          tick={{ fontSize: 11, fill: colors.slate }}
          axisLine={{ stroke: colors.line }}
          tickLine={false}
        />
        <Tooltip
          formatter={(value) => [`${value} disputes`, undefined]}
          contentStyle={{ borderRadius: 4, borderColor: colors.line, fontSize: 12 }}
        />
        <Bar dataKey="count" fill={colors.dodger} radius={[4, 4, 0, 0]} barSize={40} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// The requirement matrix is a published network rule, so it's derived from the full
// portfolio (not the selected merchant) via a >=50% majority vote per reason code —
// the raw per-dispute `required` flag has a small amount of real-world noise (matches
// the evidence_selection model's own reported 96.9% exact-match rate against it).
function RequirementMatrix({ allDisputes }) {
  const { reasonCodes, evidenceTypes, matrix } = useMemo(() => {
    const evidenceTypes = allDisputes[0]
      ? allDisputes[0].evidence_slots.map((s) => ({
          type: s.evidence_type,
          label: sentenceCase(s.label),
        }))
      : []
    const reasonCodes = [...new Set(allDisputes.map((d) => d.reason_code))].sort()

    const counts = {}
    for (const d of allDisputes) {
      for (const s of d.evidence_slots) {
        const key = `${d.reason_code}|${s.evidence_type}`
        if (!counts[key]) counts[key] = { req: 0, total: 0 }
        counts[key].total += 1
        if (s.required) counts[key].req += 1
      }
    }

    const matrix = {}
    for (const rc of reasonCodes) {
      matrix[rc] = evidenceTypes.map(({ type }) => {
        const c = counts[`${rc}|${type}`]
        return c ? c.req / c.total >= 0.5 : false
      })
    }
    return { reasonCodes, evidenceTypes, matrix }
  }, [allDisputes])

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[600px] border-collapse text-[11px]">
        <thead>
          <tr>
            <th className="border border-line bg-canvas p-2 text-left font-medium text-slate" />
            {evidenceTypes.map(({ type, label }) => (
              <th
                key={type}
                className="border border-line bg-canvas p-2 text-left font-medium text-slate"
              >
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {reasonCodes.map((rc) => (
            <tr key={rc}>
              <th className="border border-line p-2 text-left font-medium text-ink">
                {humanReason(rc)}
              </th>
              {matrix[rc].map((required, i) => (
                <td key={i} className="border border-line p-2 text-center">
                  {required && (
                    <span
                      className="mx-auto block h-3 w-3 rounded bg-ink"
                      role="img"
                      aria-label="Required"
                    />
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Evidence() {
  const { data, merchantDisputes } = useData()

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="border border-line bg-surface p-4">
          <h2 className="text-base font-semibold text-ink">
            Which documents are missing most often
          </h2>
          <div className="mt-4">
            <EvidenceGapChart disputes={merchantDisputes} />
          </div>
        </div>

        <div className="border border-line bg-surface p-4">
          <h2 className="text-base font-semibold text-ink">Packet completeness distribution</h2>
          <div className="mt-4">
            <CompletenessHistogram disputes={merchantDisputes} />
          </div>
        </div>
      </div>

      <div className="border border-line bg-surface p-4">
        <h2 className="text-base font-semibold text-ink">Requirement matrix</h2>
        <p className="mt-1 text-sm text-slate">
          A filled cell means the card network requires this document for that claim type — a
          published rule, not a guess.
        </p>
        <div className="mt-4">
          <RequirementMatrix allDisputes={data.disputes} />
        </div>
      </div>

      <p className="text-sm text-ink">
        Missing required evidence is the strongest single predictor of losing a dispute.
      </p>
    </div>
  )
}
