import client from './client'

export const analyticsApi = {
  getDashboard: () => client.get('/analytics/dashboard'),
  getProfile: () => client.get('/analytics/profile'),
  getProducts: () => client.get('/analytics/products'),
  getTrends: (period = 'monthly') => client.get(`/analytics/trends?period=${period}`),
  getSegments: () => client.get('/analytics/segments'),
  askQuestion: (question) => client.post('/analytics/chat', { question }),
}
