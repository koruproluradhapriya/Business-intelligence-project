import client from './client'

export const authApi = {
  login: (data) => client.post('/auth/login', data),
  register: (data) => client.post('/auth/register', data),
  me: () => client.get('/auth/me'),
  updateProfile: (data) => client.put('/auth/profile', data),
  getSettings: () => client.get('/settings'),
  updateSettings: (data) => client.put('/settings', data),
}
