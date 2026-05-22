import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { forecastApi } from '../api/forecast'
import { useApp } from '../context/AppContext'
import ForecastChart from '../components/charts/ForecastChart'
import { fmt } from '../utils/formatters'
import { Loader2, Upload } from 'lucide-react'

export default function ForecastPage() {
  const { notify, dataVersion } = useApp()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    forecastApi.getSalesForecast()
      .then(res => setData(res.data))
      .catch(err => {
        console.error('Forecast error:', err)
        notify('Failed to load forecast', 'error')
      })
      .finally(() => setLoading(false))
  }, [dataVersion])   // ← re-fetch after every upload

  const forecast = data?.forecast || []
  const historical = data?.historical || []
  const totalForecast = forecast.reduce((s, f) => s + (f.predicted || 0), 0)
  const isDemo = !data || historical.length === 0
  const modelCandidates = data?.modelCandidates || []
  const decomposition = data?.decomposition || []

  return (
    <div className="p-7 space-y-6 animate-fade-in">
      {isDemo && !loading && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm"
          style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)', color: '#818cf8' }}>
          <Upload size={14} />
          <span>Showing demo forecast — <Link to="/upload" className="underline font-semibold">upload sales data</Link> for AI predictions from your own data</span>
        </div>
      )}
      {!isDemo && !loading && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm"
          style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', color: '#34d399' }}>
          <Upload size={14} />
          <span>Forecast generated from <strong>your uploaded dataset</strong> using {data?.model || 'AI model'}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Next Period Prediction', value: fmt.number(forecast[0]?.predicted), change: forecast[0]?.confidence ? `${forecast[0].confidence}% confidence` : 'Adaptive forecast' },
          { label: 'Forecast Total', value: fmt.number(totalForecast), change: data?.signals?.[0] || 'Forward projection' },
          { label: 'Model Accuracy', value: data?.accuracy ? `${data.accuracy}%` : '—', change: data?.signals?.[1] || 'Model evaluation' },
        ].map((k, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            className="glass-card p-5">
            <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>{k.label}</p>
            <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              {loading ? <span className="animate-pulse">—</span> : k.value}
            </p>
            <p className="text-xs mt-1 text-emerald-400">{k.change}</p>
          </motion.div>
        ))}
      </div>

      {!loading && data?.explanation && (
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-3" style={{ color: 'var(--text-primary)' }}>Forecast Explanation</h3>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{data.explanation}</p>
          {!!data?.signals?.length && (
            <div className="mt-4 flex flex-wrap gap-2">
              {data.signals.map(signal => (
                <span key={signal} className="px-3 py-1 rounded-full text-xs" style={{ background: 'rgba(34,211,238,0.12)', color: '#67e8f9' }}>
                  {signal}
                </span>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Forecast Chart */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6">
        <div className="flex justify-between items-center mb-5">
          <div>
          <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
            Revenue Forecast — {data?.model || 'AI Model'}
          </h3>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-faint)' }}>
              {historical.length} historical periods + {forecast.length} forecast periods
            </p>
          </div>
          <div className="flex gap-5 text-xs items-center">
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 rounded-full" style={{ background: '#6366f1' }} />
              <span style={{ color: 'var(--text-faint)' }}>Historical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 rounded-full border-t border-dashed" style={{ borderColor: '#22d3ee' }} />
              <span style={{ color: 'var(--text-faint)' }}>Forecast</span>
            </div>
          </div>
        </div>
        {loading
          ? <div className="flex items-center justify-center h-48">
              <Loader2 className="animate-spin" style={{ color: '#6366f1' }} size={26} />
            </div>
          : <ForecastChart historical={historical} forecast={forecast} />
        }
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-5" style={{ color: 'var(--text-primary)' }}>Model Comparison</h3>
          {modelCandidates.length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-faint)' }}>Model scoring will appear when enough history is available.</p>
          ) : (
            <div className="space-y-3">
              {modelCandidates.map(candidate => (
                <div key={candidate.name} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{candidate.name}</p>
                    <span className="text-xs" style={{ color: '#67e8f9' }}>MAPE {candidate.mape}%</span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    MAE {fmt.number(candidate.mae)} · RMSE {fmt.number(candidate.rmse)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.06 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-5" style={{ color: 'var(--text-primary)' }}>Seasonality & Stability</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>Average Confidence</p>
              <p className="font-bold text-xl" style={{ color: 'var(--text-primary)' }}>{data?.confidenceSummary?.averageConfidence ? `${data.confidenceSummary.averageConfidence}%` : '—'}</p>
            </div>
            <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>Residual Spread</p>
              <p className="font-bold text-xl" style={{ color: 'var(--text-primary)' }}>{fmt.number(data?.confidenceSummary?.residualStd)}</p>
            </div>
          </div>
          <div className="mt-4 rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>Anomaly-aware forecasting</p>
            <p className="text-sm" style={{ color: data?.anomaliesAdjusted ? '#fbbf24' : 'var(--text-muted)' }}>
              {data?.anomaliesAdjusted ? 'Historical outliers were normalized before model training.' : 'No major outlier adjustment was needed before forecasting.'}
            </p>
          </div>
        </motion.div>
      </div>

      {/* Forecast detail table */}
      {forecast.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-5" style={{ color: 'var(--text-primary)' }}>Forecast Breakdown</h3>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                {['Period', 'Predicted Value', 'Lower Bound', 'Upper Bound', 'Confidence'].map(h => (
                  <th key={h} className="text-left pb-3 pr-6 text-[11px] font-semibold uppercase tracking-wider"
                    style={{ color: 'var(--text-faint)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {forecast.map((f, i) => (
                <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  <td className="py-3 pr-6 font-semibold" style={{ color: 'var(--text-primary)' }}>{f.period || f.month}</td>
                  <td className="py-3 pr-6 font-bold" style={{ color: '#6366f1' }}>{fmt.number(f.predicted)}</td>
                  <td className="py-3 pr-6" style={{ color: 'var(--text-muted)' }}>{fmt.number(f.lower)}</td>
                  <td className="py-3 pr-6" style={{ color: 'var(--text-muted)' }}>{fmt.number(f.upper)}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                        <div className="h-full rounded-full bg-emerald-400"
                          style={{ width: `${f.confidence || Math.max(65, 88 + i * 0.5)}%` }} />
                      </div>
                      <span className="text-xs text-emerald-400 font-semibold">{(f.confidence || Math.max(65, 88 + i * 0.5)).toFixed(1)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      )}

      {decomposition.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.24 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-5" style={{ color: 'var(--text-primary)' }}>Seasonal Decomposition Snapshot</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  {['Period', 'Observed', 'Trend', 'Seasonal', 'Residual'].map(h => (
                    <th key={h} className="text-left pb-3 pr-6 text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-faint)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {decomposition.slice(-6).map(row => (
                  <tr key={row.period} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                    <td className="py-3 pr-6 font-medium" style={{ color: 'var(--text-primary)' }}>{row.period}</td>
                    <td className="py-3 pr-6" style={{ color: 'var(--text-muted)' }}>{fmt.number(row.observed)}</td>
                    <td className="py-3 pr-6" style={{ color: 'var(--text-muted)' }}>{fmt.number(row.trend)}</td>
                    <td className="py-3 pr-6" style={{ color: 'var(--text-muted)' }}>{fmt.number(row.seasonal)}</td>
                    <td className="py-3 pr-6" style={{ color: 'var(--text-muted)' }}>{fmt.number(row.residual)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  )
}
