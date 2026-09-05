import { Info } from 'lucide-react'

export default function InfoTooltip({ text }) {
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        className="flex items-center justify-center text-slate hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
        aria-label={text}
      >
        <Info className="h-3.5 w-3.5" aria-hidden="true" />
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-full z-30 mt-2 w-72 -translate-x-1/2 border border-line bg-surface p-2.5 text-[12px] font-normal normal-case text-ink opacity-0 transition-opacity duration-100 group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {text}
      </span>
    </span>
  )
}
