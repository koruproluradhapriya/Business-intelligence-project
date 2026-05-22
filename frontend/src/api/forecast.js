import client from './client'
export const forecastApi = { getSalesForecast: () => client.get('/forecast/sales') }
