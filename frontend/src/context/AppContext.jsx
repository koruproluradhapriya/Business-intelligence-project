import { createContext, useContext, useState, useCallback, useEffect } from 'react'

const AppContext = createContext(null)

function applyTheme(theme) {
  const root = document.documentElement
  if (theme === 'light') {
    root.classList.remove('dark')
    root.setAttribute('data-theme', 'light')
  } else {
    root.classList.add('dark')
    root.setAttribute('data-theme', 'dark')
  }
}

export function AppProvider({ children }) {
  const [theme, setTheme] = useState(() => localStorage.getItem('iq_theme') || 'dark')
  const [notifications, setNotifications] = useState([])
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // ─── Data refresh token ────────────────────────────────────────────
  // Increment this whenever new data is uploaded → all pages re-fetch
  const [dataVersion, setDataVersion] = useState(0)

  const triggerDataRefresh = useCallback(() => {
    setDataVersion(v => v + 1)
  }, [])

  // Apply theme on mount + whenever it changes
  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  const toggleTheme = useCallback(() => {
    setTheme(t => {
      const next = t === 'dark' ? 'light' : 'dark'
      localStorage.setItem('iq_theme', next)
      applyTheme(next)
      return next
    })
  }, [])

  const notify = useCallback((message, type = 'info') => {
    const id = Date.now()
    setNotifications(n => [...n, { id, message, type }])
    setTimeout(() => setNotifications(n => n.filter(x => x.id !== id)), 4500)
  }, [])

  const dismissNotification = useCallback((id) => {
    setNotifications(n => n.filter(x => x.id !== id))
  }, [])

  return (
    <AppContext.Provider value={{
      theme, toggleTheme,
      notifications, notify, dismissNotification,
      sidebarCollapsed, setSidebarCollapsed,
      dataVersion, triggerDataRefresh,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppProvider')
  return ctx
}
