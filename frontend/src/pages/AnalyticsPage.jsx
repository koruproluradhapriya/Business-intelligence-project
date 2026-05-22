import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Upload } from 'lucide-react'
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { analyticsApi } from '../api/analytics'
import { useApp } from '../context/AppContext'
import { fmt } from '../utils/formatters'

export default function AnalyticsPage() {
  const { notify, dataVersion } = useApp()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    analyticsApi.getDashboard()
      .then(res => setData(res.data))
      .catch(err => {
        console.error('Analytics error:', err)
        notify('Failed to load analytics', 'error')
      })
      .finally(() => setLoading(false))
  }, [dataVersion])

  const d = data || {}
  const isDemo = d?.isDemo
  const columns = d?.profile?.columns || []
  const dimensionBreakdown = d?.dimensionBreakdown || []
  const timeSeries = d?.timeSeries || []
  const anomalies = d?.anomalies || []
  const executiveSummary = d?.executiveSummary || {}

  return (
    <div className="p-7 space-y-6 animate-fade-in">
      {isDemo && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(37,99,235,0.1)', border: '1px solid rgba(37,99,235,0.2)', color: '#93c5fd' }}>
          <Upload size={14} />
          <span>Showing demo data. <Link to="/upload" className="underline font-semibold">Upload a dataset</Link> for real analytics.</span>
        </div>
      )}

      {!!executiveSummary.overview && (
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-3" style={{ color: 'var(--text-primary)' }}>Executive Summary</h3>
          <p className="text-sm leading-relaxed mb-4" style={{ color: 'var(--text-muted)' }}>{executiveSummary.overview}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>Risks</p>
              {(executiveSummary.risks || []).map(risk => (
                <p key={risk} className="text-sm mb-2 last:mb-0" style={{ color: 'var(--text-muted)' }}>{risk}</p>
              ))}
            </div>
            <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>Opportunities</p>
              {(executiveSummary.opportunities || []).map(item => (
                <p key={item} className="text-sm mb-2 last:mb-0" style={{ color: 'var(--text-muted)' }}>{item}</p>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Detected Columns</h3>
          <div className="space-y-3">
            {columns.map(column => (
              <div key={column.name} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{column.name}</p>
                  <span className="text-[10px] uppercase tracking-[0.15em]" style={{ color: 'var(--text-faint)' }}>{column.detectedType}</span>
                </div>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Semantic label: {column.semanticLabel || 'unmapped'} · Missing: {fmt.number(column.missingCount)} · Unique: {fmt.number(column.uniqueCount)}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Top Contributors</h3>
          {loading ? (
            <div className="h-72 rounded-xl animate-pulse" style={{ background: 'rgba(255,255,255,0.04)' }} />
          ) : dimensionBreakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={dimensionBreakdown}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm" style={{ color: 'var(--text-faint)' }}>No dimension breakdown is available for this dataset yet.</p>
          )}
        </motion.div>
      </div>

      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6">
        <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Trend Table</h3>
        {timeSeries.length === 0 ? (
          <p className="text-sm" style={{ color: 'var(--text-faint)' }}>No time-series fields were detected in this upload.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                {['Period', 'Value'].map(header => (
                  <th key={header} className="text-left pb-3 pr-5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-faint)' }}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeSeries.map(row => (
                <tr key={row.period} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  <td className="py-3 pr-5 font-medium" style={{ color: 'var(--text-primary)' }}>{row.period}</td>
                  <td className="py-3 pr-5" style={{ color: 'var(--text-muted)' }}>{fmt.number(row.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-card p-6">
        <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Anomaly Review</h3>
        {anomalies.length === 0 ? (
          <p className="text-sm" style={{ color: 'var(--text-faint)' }}>No major anomalies were detected in the primary trend.</p>
        ) : (
          <div className="space-y-3">
            {anomalies.map(item => (
              <div key={`${item.date}-${item.type}`} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{item.type} in {item.date}</p>
                  <span className="text-xs" style={{ color: item.severity === 'high' ? '#fca5a5' : '#fcd34d' }}>{item.severity}</span>
                </div>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Actual {fmt.number(item.value)} vs expected {fmt.number(item.expected)} · delta {fmt.number(item.delta)} · z-score {item.zScore}
                </p>
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}
