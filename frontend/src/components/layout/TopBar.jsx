import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useApp } from '../../context/AppContext'
import { Sun, Moon, Bell } from 'lucide-react'

const TITLES = {
  '/': 'Dashboard',
  '/analytics': 'Analytics',
  '/forecast': 'Forecasting',
  '/inventory': 'Inventory',
  '/recommendations': 'AI Insights',
  '/upload': 'Upload Data',
  '/settings': 'Settings',
}

export default function TopBar() {
  const { pathname } = useLocation()
  const { user } = useAuth()
  const { theme, toggleTheme } = useApp()
  const initials = user?.name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U'

  return (
    <header className="h-16 flex-shrink-0 flex items-center justify-between px-7 bg-surface-800 border-b border-white/[0.06]">
      <div>
        <h1 className="text-white font-semibold text-base tracking-tight">{TITLES[pathname] || 'InsightIQ'}</h1>
        <p className="text-white/30 text-xs">Last updated just now</p>
      </div>
      <div className="flex items-center gap-3">
        <button onClick={toggleTheme} className="p-2 rounded-xl text-white/40 hover:text-white hover:bg-white/[0.06] transition-all">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <button className="relative p-2 rounded-xl text-white/40 hover:text-white hover:bg-white/[0.06] transition-all">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-brand-500 rounded-full" />
        </button>
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-cyan-400 flex items-center justify-center text-white font-bold text-xs cursor-pointer">
          {initials}
        </div>
      </div>
    </header>
  )
}
