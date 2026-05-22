import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '../api/auth'
import client from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('iq_token')
    if (token) {
      client.defaults.headers.common['Authorization'] = `Bearer ${token}`
      authApi.me()
        .then(res => setUser(res.data.user))
        .catch(() => { localStorage.removeItem('iq_token'); delete client.defaults.headers.common['Authorization'] })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await authApi.login({ email, password })
    const { user, accessToken } = res.data
    localStorage.setItem('iq_token', accessToken)
    client.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
    setUser(user)
    return user
  }, [])

  const register = useCallback(async (data) => {
    const res = await authApi.register(data)
    const { user, accessToken } = res.data
    localStorage.setItem('iq_token', accessToken)
    client.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
    setUser(user)
    return user
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('iq_token')
    delete client.defaults.headers.common['Authorization']
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
