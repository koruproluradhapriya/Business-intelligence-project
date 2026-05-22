import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { useApp } from '../../context/AppContext'
import Notification from '../ui/Notification'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  const { notifications, dismissNotification } = useApp()

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-surface-900">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-cyan-400 flex items-center justify-center text-white font-black text-lg">IQ</div>
        <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    </div>
  )

  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="flex h-screen bg-surface-900 overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
      {/* Notifications */}
      <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
        {notifications.map(n => (
          <Notification key={n.id} {...n} onDismiss={dismissNotification} />
        ))}
      </div>
    </div>
  )
}
