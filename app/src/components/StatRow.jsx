export default function StatRow({ items }) {
  return (
    <div className="grid grid-cols-4 border border-line bg-surface">
      {items.map((item, index) => (
        <div key={item.label} className={`p-4 ${index > 0 ? 'border-l border-line' : ''}`}>
          <div className="text-[11px] text-slate">{item.label}</div>
          <div className="num mt-1 text-[28px] font-semibold text-ink">{item.value}</div>
        </div>
      ))}
    </div>
  )
}
