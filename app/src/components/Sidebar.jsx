import { NavLink } from 'react-router-dom'
import { FileText, HelpCircle, LayoutDashboard, ShieldCheck } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/disputes', label: 'Disputes', icon: FileText },
  { to: '/evidence', label: 'Evidence', icon: ShieldCheck },
  { to: '/methodology', label: 'How it works', icon: HelpCircle },
]

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 flex w-16 flex-col bg-prussian shadow-[2px_0_4px_rgba(0,0,0,0.15)] md:w-60">
      <div className="flex items-center justify-center px-2 py-5 md:block md:px-4">
        <span className="flex h-8 w-8 items-center justify-center bg-white/10 text-sm font-semibold text-white md:hidden">
          S
        </span>
        <div className="hidden text-[20px] font-semibold text-white md:block">SaHaYa</div>
        <div className="hidden text-[11px] font-normal text-white/60 md:block">
          saboot hai yahan
        </div>
      </div>
      <nav className="flex-1 px-2">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              title={item.label}
              className={({ isActive }) =>
                `flex items-center justify-center gap-3 border-l-2 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger md:justify-start ${
                  isActive
                    ? 'border-dodger bg-white/5 text-white'
                    : 'border-transparent text-white/70 hover:text-white'
                }`
              }
            >
              <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
              <span className="hidden md:inline">{item.label}</span>
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
