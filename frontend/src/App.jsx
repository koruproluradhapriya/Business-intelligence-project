import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { AppProvider } from './context/AppContext'
import ProtectedRoute from './components/layout/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import AnalyticsPage from './pages/AnalyticsPage'
import ForecastPage from './pages/ForecastPage'
import InventoryPage from './pages/InventoryPage'
import RecommendationsPage from './pages/RecommendationsPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/forecast" element={<ForecastPage />} />
              <Route path="/inventory" element={<InventoryPage />} />
              <Route path="/recommendations" element={<RecommendationsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
