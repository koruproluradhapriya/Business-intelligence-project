import client from './client'
export const inventoryApi = { getStatus: () => client.get('/inventory/status') }
