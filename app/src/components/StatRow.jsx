// 2 columns below md (768px), 4 above — dividers switch from "top border on
// row 2" to "left border on every column" at the same breakpoint the grid reflows.
function borderClasses(index) {
  const rightColMobile = index % 2 === 1
  const secondRowMobile = index >= 2
  const notFirstDesktop = index >= 1
  return [
    rightColMobile && 'border-l',
    secondRowMobile && 'border-t',
    'md:border-t-0',
    notFirstDesktop && 'md:border-l',
  ]
    .filter(Boolean)
    .join(' ')
}

export default function StatRow({ items }) {
  return (
    <div className="grid grid-cols-2 border border-line bg-surface md:grid-cols-4">
      {items.map((item, index) => (
        <div key={item.label} className={`border-line p-4 ${borderClasses(index)}`}>
          <div className="text-[11px] text-slate">{item.label}</div>
          <div className="num mt-1 text-[28px] font-semibold text-ink">{item.value}</div>
        </div>
      ))}
    </div>
  )
}
