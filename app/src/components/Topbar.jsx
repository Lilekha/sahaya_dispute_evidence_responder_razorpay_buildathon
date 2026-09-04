import MerchantSwitcher from './MerchantSwitcher'

export default function Topbar() {
  return (
    <header className="flex min-h-14 items-center justify-end border-b border-line bg-surface px-6 py-2">
      <div className="flex flex-col items-end gap-1">
        <span className="text-[11px] text-slate">Account</span>
        <MerchantSwitcher />
      </div>
    </header>
  )
}
