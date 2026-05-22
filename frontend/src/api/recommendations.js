import client from './client'
export const recommendationsApi = {
  get: (refresh = false) => client.get(`/recommendations?refresh=${refresh}`),
}
