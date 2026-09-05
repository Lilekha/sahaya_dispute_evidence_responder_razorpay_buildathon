import { matchPath, useLocation } from 'react-router-dom'
import { useData } from '../context/DataContext'
import MerchantSwitcher from './MerchantSwitcher'

function usePageHeader() {
  const { pathname } = useLocation()
  const { selectedMerchant, dataAsOf } = useData()
  const merchantName = selectedMerchant?.name ?? ''

  if (pathname === '/') {
    return {
      title: 'Dispute overview',
      description: selectedMerchant
        ? `${merchantName} · ${selectedMerchant.n_disputes} open disputes · Data as of ${dataAsOf}`
        : '',
    }
  }
  if (pathname === '/disputes') {
    return {
      title: 'Disputes',
      description: selectedMerchant
        ? `Every open dispute for ${merchantName}, with our recommendation.`
        : '',
    }
  }
  if (matchPath('/disputes/:id', pathname)) {
    return {
      title: 'Dispute details',
      description: 'The evidence, the economics, and why we recommend this action.',
    }
  }
  if (pathname === '/evidence') {
    return {
      title: 'Evidence',
      description: 'Which documents this merchant holds, and which the networks require.',
    }
  }
  if (pathname === '/methodology') {
    return {
      title: 'How SaHaYa works',
      description: 'What the system measures, and how honestly it performs.',
    }
  }
  return null
}

export default function Topbar() {
  const header = usePageHeader()

  return (
    <header className="flex min-h-14 items-center justify-between gap-4 border-b border-line bg-surface px-6 py-2">
      <div className="min-w-0">
        {header && (
          <>
            <h1 className="truncate text-[16px] font-semibold text-ink">{header.title}</h1>
            <p className="truncate text-[13px] text-slate">{header.description}</p>
          </>
        )}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <span className="text-[11px] text-slate">Account</span>
        <MerchantSwitcher />
      </div>
    </header>
  )
}
