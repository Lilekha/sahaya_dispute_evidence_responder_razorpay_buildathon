import MerchantSwitcher from './MerchantSwitcher'

export default function Topbar() {
  return (
    <header className="flex h-14 items-center border-b border-line bg-surface px-6">
      <MerchantSwitcher />
    </header>
  )
}
