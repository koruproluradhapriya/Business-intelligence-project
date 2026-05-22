import { NavLink } from 'react-router-dom'
import { useApp } from '../../context/AppContext'
import { useAuth } from '../../context/AuthContext'
import {
  LayoutDashboard, BarChart3, TrendingUp, Package,
  Lightbulb, Upload, Settings, ChevronLeft, ChevronRight, LogOut
} from 'lucide-react'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/forecast', icon: TrendingUp, label: 'Forecasting' },
  { to: '/inventory', icon: Package, label: 'Inventory' },
  { to: '/recommendations', icon: Lightbulb, label: 'AI Insights' },
  { to: '/upload', icon: Upload, label: 'Upload Data' },
]

export default function Sidebar() {
  const { sidebarCollapsed, setSidebarCollapsed } = useApp()
  const { logout, user } = useAuth()
  const c = sidebarCollapsed

  return (
    <aside className={`${c ? 'w-[72px]' : 'w-60'} flex-shrink-0 flex flex-col bg-surface-800 border-r border-white/[0.06] transition-all duration-300 overflow-hidden`}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/[0.06]">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-cyan-400 flex items-center justify-center text-white font-black text-sm flex-shrink-0">IQ</div>
        {!c && <div>
          <div className="text-white font-bold text-sm tracking-tight">InsightIQ</div>
          <div className="text-white/30 text-[10px]">Analytics Platform</div>
        </div>}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group
               ${isActive ? 'bg-brand-500/20 text-brand-400' : 'text-white/50 hover:text-white hover:bg-white/[0.05]'}`
            }>
            <Icon size={18} className="flex-shrink-0" />
            {!c && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="py-3 px-2 border-t border-white/[0.06] space-y-0.5">
        <NavLink to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150
             ${isActive ? 'bg-brand-500/20 text-brand-400' : 'text-white/50 hover:text-white hover:bg-white/[0.05]'}`
          }>
          <Settings size={18} className="flex-shrink-0" />
          {!c && <span>Settings</span>}
        </NavLink>

        <button onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/40 hover:text-red-400 hover:bg-red-500/10 transition-all duration-150">
          <LogOut size={18} className="flex-shrink-0" />
          {!c && <span>Logout</span>}
        </button>

        <button onClick={() => setSidebarCollapsed(!c)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-white/30 hover:text-white/60 hover:bg-white/[0.04] transition-all duration-150">
          {c ? <ChevronRight size={16} className="flex-shrink-0" /> : <><ChevronLeft size={16} /><span>Collapse</span></>}
        </button>
      </div>
    </aside>
  )
}
