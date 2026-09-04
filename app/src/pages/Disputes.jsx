import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useData } from '../context/DataContext'
import { inr, pct, humanReason, daysLeft } from '../lib/format'
import RecommendationBadge from '../components/RecommendationBadge'
import ProbabilityBar from '../components/ProbabilityBar'

const MARGINAL_THRESHOLD = 0.05

export default function Disputes() {
  const { merchantDisputes } = useData()
  const [searchParams, setSearchParams] = useSearchParams()

  const recommendationFilter = searchParams.get('recommendation') ?? 'all'
  const reasonFilter = searchParams.get('reason') ?? 'all'
  const sortBy = searchParams.get('sort') ?? 'deadline'

  const reasonOptions = useMemo(() => {
    const set = new Set(merchantDisputes.map((d) => d.reason_code))
    return [...set].sort()
  }, [merchantDisputes])

  const filtered = useMemo(() => {
    let list = merchantDisputes
    if (recommendationFilter !== 'all') {
      list = list.filter((d) => d.recommendation === recommendationFilter)
    }
    if (reasonFilter !== 'all') {
      list = list.filter((d) => d.reason_code === reasonFilter)
    }
    return list
  }, [merchantDisputes, recommendationFilter, reasonFilter])

  const sorted = useMemo(() => {
    const list = [...filtered]
    if (sortBy === 'amount') {
      list.sort((a, b) => b.dispute_amount - a.dispute_amount)
    } else if (sortBy === 'win_probability') {
      list.sort((a, b) => b.p_win - a.p_win)
    } else {
      list.sort((a, b) => a.days_to_deadline - b.days_to_deadline)
    }
    return list
  }, [filtered, sortBy])

  function updateParam(key, value) {
    const next = new URLSearchParams(searchParams)
    if (value == null || value === 'all' || value === 'deadline') {
      next.delete(key)
    } else {
      next.set(key, value)
    }
    setSearchParams(next, { replace: true })
  }

  function clearFilters() {
    setSearchParams({}, { replace: true })
  }

  const hasActiveFilters = recommendationFilter !== 'all' || reasonFilter !== 'all'

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-4 text-sm">
        <label className="flex items-center gap-2">
          <span className="text-slate">Recommendation</span>
          <select
            value={recommendationFilter}
            onChange={(e) => updateParam('recommendation', e.target.value)}
            className="border border-line bg-surface px-2 py-1.5 text-sm text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
          >
            <option value="all">All</option>
            <option value="CONTEST">Contest</option>
            <option value="ACCEPT">Accept</option>
          </select>
        </label>

        <label className="flex items-center gap-2">
          <span className="text-slate">Reason</span>
          <select
            value={reasonFilter}
            onChange={(e) => updateParam('reason', e.target.value)}
            className="border border-line bg-surface px-2 py-1.5 text-sm text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
          >
            <option value="all">All</option>
            {reasonOptions.map((code) => (
              <option key={code} value={code}>
                {humanReason(code)}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2">
          <span className="text-slate">Sort by</span>
          <select
            value={sortBy}
            onChange={(e) => updateParam('sort', e.target.value)}
            className="border border-line bg-surface px-2 py-1.5 text-sm text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
          >
            <option value="deadline">Deadline</option>
            <option value="amount">Amount</option>
            <option value="win_probability">Win probability</option>
          </select>
        </label>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearFilters}
            className="text-sm text-dodger underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
          >
            Clear filters
          </button>
        )}
      </div>

      {sorted.length === 0 ? (
        <div className="border border-line bg-surface p-8 text-center text-sm text-slate">
          No disputes match these filters.{' '}
          <button
            type="button"
            onClick={clearFilters}
            className="text-dodger underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
          >
            Clear them
          </button>{' '}
          to see all {merchantDisputes.length}.
        </div>
      ) : (
        <div className="overflow-x-auto border border-line bg-surface">
          <table className="w-full min-w-[980px] text-[13px]">
            <thead>
              <tr className="border-b border-line text-left text-[11px] text-slate">
                <th className="px-3 py-2 font-medium">Dispute ID</th>
                <th className="w-32 px-3 py-2 font-medium">Reason</th>
                <th className="px-3 py-2 font-medium">Customer</th>
                <th className="px-3 py-2 text-right font-medium">Amount</th>
                <th className="px-3 py-2 font-medium">Win probability</th>
                <th className="px-3 py-2 text-right font-medium">Break-even</th>
                <th className="px-3 py-2 font-medium">Recommendation</th>
                <th className="px-3 py-2 text-right font-medium">Deadline</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((d) => {
                const isMarginal = Math.abs(d.p_win - d.breakeven) <= MARGINAL_THRESHOLD
                const isUrgent = d.days_to_deadline <= 3
                return (
                  <tr
                    key={d.dispute_id}
                    className="relative h-11 border-b border-line last:border-b-0 hover:bg-canvas"
                  >
                    <td className="px-3 align-middle">
                      <Link
                        to={`/disputes/${d.dispute_id}`}
                        className="absolute inset-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger focus-visible:ring-inset"
                        aria-label={`View dispute ${d.dispute_id}`}
                      />
                      <span className="num relative text-ink">{d.dispute_id}</span>
                    </td>
                    <td className="w-32 truncate px-3 align-middle text-ink">
                      {humanReason(d.reason_code)}
                    </td>
                    <td className="px-3 align-middle text-ink">
                      {d.customer_name ? `${d.customer_name} · ${d.customer_city}` : '—'}
                    </td>
                    <td className="num px-3 text-right align-middle text-ink">
                      {inr(d.dispute_amount)}
                    </td>
                    <td className="px-3 align-middle">
                      <span className="flex items-center gap-2">
                        <span className={`num ${isMarginal ? 'text-ink' : 'text-slate'}`}>
                          {pct(d.p_win)}
                        </span>
                        <ProbabilityBar value={d.p_win} />
                      </span>
                    </td>
                    <td
                      className={`num px-3 text-right align-middle ${
                        isMarginal ? 'text-ink' : 'text-slate'
                      }`}
                    >
                      {pct(d.breakeven)}
                    </td>
                    <td className="px-3 align-middle">
                      <RecommendationBadge recommendation={d.recommendation} />
                    </td>
                    <td
                      className={`num px-3 text-right align-middle ${
                        isUrgent ? 'text-gap' : 'text-ink'
                      }`}
                    >
                      {daysLeft(d.days_to_deadline)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
