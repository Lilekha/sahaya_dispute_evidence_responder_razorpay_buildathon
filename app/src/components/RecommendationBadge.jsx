export default function RecommendationBadge({ recommendation }) {
  const isContest = recommendation === 'CONTEST'
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${
        isContest ? 'bg-contest/10 text-contest' : 'bg-accept/10 text-accept'
      }`}
    >
      {isContest ? 'Contest' : 'Accept'}
    </span>
  )
}
