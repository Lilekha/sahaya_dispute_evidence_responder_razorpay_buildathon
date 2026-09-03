import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Overview' },
  { to: '/disputes', label: 'Disputes' },
  { to: '/evidence', label: 'Evidence' },
  { to: '/methodology', label: 'How it works' },
]

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 flex w-60 flex-col bg-prussian shadow-[2px_0_4px_rgba(0,0,0,0.15)]">
      <div className="px-4 py-5">
        <div className="text-[20px] font-semibold text-white">SaHaYa</div>
        <div className="text-[11px] font-normal text-white/60">saboot hai yahan</div>
      </div>
      <nav className="flex-1 px-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `block border-l-2 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dodger ${
                isActive
                  ? 'border-dodger bg-white/5 text-white'
                  : 'border-transparent text-white/70 hover:text-white'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
