import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { matchPath, useLocation, useNavigate } from 'react-router-dom'
import { useData } from '../context/DataContext'
import { pct } from '../lib/format'
import MerchantAvatar from './MerchantAvatar'

function humanizeArchetype(archetype) {
  if (!archetype) return ''
  const spaced = archetype.replace(/_/g, ' ')
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

function MaturityBar({ value }) {
  const widthPct = Math.round(Math.max(0, Math.min(1, value ?? 0)) * 100)
  return (
    <span className="flex items-center gap-2">
      <span className="h-1.5 w-16 overflow-hidden rounded border border-line bg-canvas">
        <span className="block h-full bg-dodger" style={{ width: `${widthPct}%` }} />
      </span>
      <span className="num text-[11px] text-slate">{pct(value, 0)}</span>
    </span>
  )
}

export default function MerchantSwitcher() {
  const { data, selectedMerchant, setSelectedMerchant } = useData()
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const containerRef = useRef(null)
  const triggerRef = useRef(null)
  const optionRefs = useRef([])
  const listboxId = useId()

  const sortedMerchants = useMemo(() => {
    if (!data?.merchants) return []
    return [...data.merchants].sort((a, b) => a.demo_priority - b.demo_priority)
  }, [data])

  optionRefs.current = []

  useEffect(() => {
    if (!open) return

    function handlePointerDown(event) {
      if (!containerRef.current?.contains(event.target)) setOpen(false)
    }
    function handleFocusIn(event) {
      if (!containerRef.current?.contains(event.target)) setOpen(false)
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('focusin', handleFocusIn)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('focusin', handleFocusIn)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const selectedIndex = sortedMerchants.findIndex(
      (m) => m.merchant_id === selectedMerchant?.merchant_id,
    )
    optionRefs.current[selectedIndex >= 0 ? selectedIndex : 0]?.focus()
  }, [open, sortedMerchants, selectedMerchant])

  if (!selectedMerchant) return null

  function focusOptionAt(index) {
    optionRefs.current[index]?.focus()
  }

  function handleTriggerKeyDown(event) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      setOpen(true)
    }
  }

  function handleOptionKeyDown(event, index) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      focusOptionAt((index + 1) % sortedMerchants.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      focusOptionAt((index - 1 + sortedMerchants.length) % sortedMerchants.length)
    } else if (event.key === 'Escape') {
      event.preventDefault()
      setOpen(false)
      triggerRef.current?.focus()
    }
  }

  function handleSelect(merchant) {
    setSelectedMerchant(merchant)
    setOpen(false)
    triggerRef.current?.focus()
    if (matchPath('/disputes/:id', location.pathname)) {
      navigate('/disputes')
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={handleTriggerKeyDown}
        className="flex max-w-[240px] items-center gap-2 border border-line px-3 py-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger"
      >
        <span className="min-w-0 flex-1">
          <span className="block truncate text-right text-sm font-medium text-ink">
            {selectedMerchant.name}
          </span>
          <span className="block truncate text-right text-[11px] text-slate">
            {humanizeArchetype(selectedMerchant.archetype)}
          </span>
        </span>
        <MerchantAvatar key={selectedMerchant.merchant_id} merchant={selectedMerchant} size={32} />
        <ChevronDown
          aria-hidden="true"
          className={`h-4 w-4 shrink-0 text-slate transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div
          id={listboxId}
          role="listbox"
          aria-label="Select merchant"
          className="absolute right-0 top-full z-20 mt-2 max-h-[70vh] w-[280px] divide-y divide-line overflow-y-auto border border-line bg-surface"
        >
          {sortedMerchants.map((merchant, index) => {
            const isSelected = merchant.merchant_id === selectedMerchant.merchant_id
            return (
              <button
                key={merchant.merchant_id}
                ref={(el) => (optionRefs.current[index] = el)}
                type="button"
                role="option"
                aria-selected={isSelected}
                tabIndex={-1}
                onClick={() => handleSelect(merchant)}
                onKeyDown={(event) => handleOptionKeyDown(event, index)}
                className={`block w-full px-3 py-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger ${
                  isSelected ? 'bg-dodger/5' : 'hover:bg-canvas'
                }`}
              >
                <span className="flex items-center gap-3">
                  <MerchantAvatar merchant={merchant} size={28} />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink">
                    {merchant.name}
                  </span>
                  <Check
                    aria-hidden="true"
                    className={`h-4 w-4 shrink-0 text-dodger ${isSelected ? 'opacity-100' : 'opacity-0'}`}
                  />
                </span>
                <span className="mt-1 flex items-center justify-between gap-3 pl-10 text-[11px] text-slate">
                  <span className="truncate">{humanizeArchetype(merchant.archetype)}</span>
                  <span className="num shrink-0">{merchant.n_disputes} disputes</span>
                </span>
                <span className="mt-1.5 block pl-10">
                  <MaturityBar value={merchant.documentation_maturity} />
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
