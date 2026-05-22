import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token automatically
client.interceptors.request.use(config => {
  const token = localStorage.getItem('iq_token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

// Handle 401 globally
client.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('iq_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
