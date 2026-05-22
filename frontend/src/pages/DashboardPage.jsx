import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  AlertTriangle, Bot, Database, Lightbulb, Loader2, MessageSquareText, RefreshCw, Sparkles, Upload,
} from 'lucide-react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer,
  Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from 'recharts'
import { analyticsApi } from '../api/analytics'
import { forecastApi } from '../api/forecast'
import { useApp } from '../context/AppContext'
import { fmt } from '../utils/formatters'

const COLORS = ['#2563eb', '#14b8a6', '#f59e0b', '#ef4444', '#8b5cf6', '#22c55e', '#f97316', '#06b6d4']

function ChartCard({ chart }) {
  const series = chart.series || []
  const primarySeries = series[0]?.key

  const renderTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div className="glass-card px-3 py-2 text-xs">
        <p className="font-semibold text-white/80 mb-1">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color || '#fff' }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    )
  }

  return (
    <div className="glass-card p-5">
      <h3 className="font-semibold text-sm mb-1" style={{ color: 'var(--text-primary)' }}>{chart.title}</h3>
      <p className="text-xs mb-4" style={{ color: 'var(--text-faint)' }}>{chart.chartType} visualization selected automatically</p>
      <ResponsiveContainer width="100%" height={260}>
        {chart.chartType === 'line' ? (
          <LineChart data={chart.data}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey={chart.xKey} tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={renderTooltip} />
            <Legend />
            {series.map((item, index) => (
              <Line key={item.key} type="monotone" dataKey={item.key} name={item.label} stroke={COLORS[index % COLORS.length]} strokeWidth={2.5} dot={false} />
            ))}
          </LineChart>
        ) : chart.chartType === 'area' ? (
          <AreaChart data={chart.data}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey={chart.xKey} tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={renderTooltip} />
            <Legend />
            {series.map((item, index) => (
              <Area key={item.key} type="monotone" dataKey={item.key} name={item.label} stroke={COLORS[index % COLORS.length]} fill={COLORS[index % COLORS.length]} fillOpacity={0.18} strokeWidth={2.5} />
            ))}
          </AreaChart>
        ) : chart.chartType === 'pie' ? (
          <PieChart>
            <Tooltip content={renderTooltip} />
            <Pie data={chart.data} dataKey={primarySeries} nameKey={chart.xKey} innerRadius={52} outerRadius={86} paddingAngle={2}>
              {chart.data.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
            </Pie>
            <Legend />
          </PieChart>
        ) : chart.chartType === 'scatter' || chart.chartType === 'heatmap' ? (
          <ScatterChart>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey={chart.xKey} type="category" tick={{ fill: '#7c8797', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis dataKey={chart.chartType === 'heatmap' ? 'y' : primarySeries} type={chart.chartType === 'heatmap' ? 'category' : 'number'} tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={renderTooltip} />
            <Scatter data={chart.data} fill={chart.chartType === 'heatmap' ? '#f59e0b' : '#22d3ee'} />
          </ScatterChart>
        ) : (
          <BarChart data={chart.data}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey={chart.xKey} tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#7c8797', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={renderTooltip} />
            <Legend />
            {series.map((item, index) => (
              <Bar key={item.key} dataKey={item.key} name={item.label} radius={[8, 8, 0, 0]} fill={COLORS[index % COLORS.length]} />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}

export default function DashboardPage() {
  const { notify, dataVersion } = useApp()
  const [data, setData] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(true)
  const [question, setQuestion] = useState('')
  const [chatAnswer, setChatAnswer] = useState(null)
  const [chatLoading, setChatLoading] = useState(false)

  const loadDashboard = () => {
    setLoading(true)
    Promise.all([analyticsApi.getDashboard(), forecastApi.getSalesForecast()])
      .then(([dashboardRes, forecastRes]) => {
        setData(dashboardRes.data)
        setForecast(forecastRes.data)
      })
      .catch(err => {
        console.error('Dashboard error:', err)
        notify('Failed to load dashboard data', 'error')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadDashboard()
  }, [dataVersion])

  const askQuestion = async () => {
    if (!question.trim()) return
    setChatLoading(true)
    try {
      const res = await analyticsApi.askQuestion(question)
      setChatAnswer(res.data)
    } catch (err) {
      notify(err.response?.data?.error || 'Failed to ask question', 'error')
    } finally {
      setChatLoading(false)
    }
  }

  const d = data || {}
  const dataset = d.dataset || {}
  const kpis = d.kpis || []
  const charts = d.charts || []
  const insights = d.insights || []
  const recommendations = d.recommendations || []
  const anomalies = d.anomalies || []
  const profile = d.profile || {}
  const schemaMapping = d.schemaMapping || {}
  const inferredSchema = d.inferredSchema || {}
  const forecastRows = forecast?.forecast || d.forecast?.forecast || []

  return (
    <div className="p-7 space-y-6 animate-fade-in">
      {d.isDemo ? (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(37,99,235,0.1)', border: '1px solid rgba(37,99,235,0.2)', color: '#93c5fd' }}>
          <AlertTriangle size={15} />
          <span>Demo dataset is active. <Link to="/upload" className="underline font-semibold hover:opacity-80">Upload a real file</Link> to generate a live intelligence dashboard.</span>
        </div>
      ) : (
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm" style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', color: '#6ee7b7' }}>
          <Upload size={14} />
          <span>Dashboard is running on <strong>{dataset.name || 'your uploaded dataset'}</strong></span>
          <button onClick={loadDashboard} className="ml-auto flex items-center gap-1.5 hover:opacity-70 transition-opacity">
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        {kpis.map((card, index) => (
          <motion.div key={`${card.label}-${index}`} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.04 }} className="glass-card p-5">
            <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>{card.label}</p>
            <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              {loading ? '—' : fmt.metric(card.value, card.format)}
            </p>
            <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
              {card.change == null ? 'Auto-detected from uploaded data' : `${fmt.percent(card.change)} vs comparison period`}
            </p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Database size={16} style={{ color: '#22d3ee' }} />
            <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Dataset Understanding</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ['Rows', profile.rowCount],
              ['Columns', profile.columnCount],
              ['Missing Cells', profile.missingValueCells],
              ['Duplicate Rows', profile.duplicateRows],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>{label}</p>
                <p className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>{fmt.number(value)}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {(profile.columns || []).slice(0, 12).map(column => (
              <span key={column.name} className="px-3 py-1 rounded-full text-xs" style={{ background: 'rgba(37,99,235,0.12)', color: '#bfdbfe' }}>
                {column.name} · {column.detectedType}{column.semanticLabel ? ` · ${column.semanticLabel}` : ''}{column.semanticConfidence ? ` · ${Math.round(column.semanticConfidence * 100)}%` : ''}
              </span>
            ))}
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bot size={16} style={{ color: '#f59e0b' }} />
            <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Chat With Data</h3>
          </div>
          <div className="space-y-3">
            <textarea
              value={question}
              onChange={e => setQuestion(e.target.value)}
              rows={4}
              placeholder="Why did revenue drop? Which segment performed best? Predict the next period."
              className="w-full rounded-xl px-3 py-2 text-sm bg-white/5 border border-white/10 outline-none"
              style={{ color: 'var(--text-primary)' }}
            />
            <button onClick={askQuestion} disabled={chatLoading} className="btn-primary w-full flex items-center justify-center gap-2 py-2.5">
              {chatLoading ? <Loader2 size={15} className="animate-spin" /> : <MessageSquareText size={15} />}
              Ask
            </button>
            <div className="flex flex-wrap gap-2">
              {(d.chatSuggestions || []).map(suggestion => (
                <button key={suggestion} onClick={() => setQuestion(suggestion)} className="text-xs px-2.5 py-1 rounded-full border border-white/10 hover:border-white/20" style={{ color: 'var(--text-muted)' }}>
                  {suggestion}
                </button>
              ))}
            </div>
            <div className="rounded-xl p-4 min-h-[120px]" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>AI-style answer</p>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                {chatAnswer?.answer || 'Ask a question about the uploaded dataset to get a concise business explanation.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {charts.map(chart => <ChartCard key={chart.id} chart={chart} />)}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Schema Mapping</h3>
          {Object.keys(schemaMapping).length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-faint)' }}>No strong business concepts were inferred yet.</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(schemaMapping).slice(0, 8).map(([label, columns]) => (
                <div key={label} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-xs uppercase tracking-[0.15em] mb-1" style={{ color: 'var(--text-faint)' }}>{label}</p>
                  <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{columns.join(', ')}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Data Quality Details</h3>
          <div className="space-y-3">
            {(profile.outliers || []).slice(0, 5).map(item => (
              <div key={item.column} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <p className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>{item.column}</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.count} outliers detected</p>
              </div>
            ))}
            {(!profile.outliers || profile.outliers.length === 0) && (
              <p className="text-sm" style={{ color: 'var(--text-faint)' }}>No major numeric outlier clusters were detected.</p>
            )}
            <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>Inferred columns</p>
              <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{Object.keys(inferredSchema).length}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={16} style={{ color: '#a78bfa' }} />
            <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Business Insights</h3>
          </div>
          <div className="space-y-3">
            {insights.map((insight, index) => (
              <div key={`${insight.title}-${index}`} className="rounded-xl p-4 border border-white/8" style={{ background: 'rgba(255,255,255,0.03)' }}>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{insight.title}</p>
                  <span className="text-[10px] uppercase tracking-[0.15em]" style={{ color: 'var(--text-faint)' }}>{insight.category}</span>
                </div>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{insight.summary}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb size={16} style={{ color: '#34d399' }} />
            <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>Recommendations</h3>
          </div>
          <div className="space-y-3">
            {recommendations.map((rec, index) => (
              <div key={`${rec.title}-${index}`} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                <p className="font-semibold text-sm mb-1" style={{ color: 'var(--text-primary)' }}>{rec.title}</p>
                <p className="text-xs leading-relaxed mb-2" style={{ color: 'var(--text-muted)' }}>{rec.text}</p>
                {rec.action && <span className="text-[11px] font-semibold" style={{ color: '#6ee7b7' }}>{rec.action}</span>}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Forecast Outlook</h3>
          {forecastRows.length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-faint)' }}>A forecast will appear automatically when the dataset contains enough time-based history.</p>
          ) : (
            <div className="space-y-3">
              {forecastRows.slice(0, 6).map(row => (
                <div key={row.period} className="flex items-center justify-between rounded-xl px-4 py-3" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{row.period}</span>
                  <span className="text-sm" style={{ color: '#93c5fd' }}>{fmt.number(row.predicted)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card p-6">
          <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Anomalies & Alerts</h3>
          {anomalies.length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-faint)' }}>No major anomalies were flagged from the current primary trend.</p>
          ) : (
            <div className="space-y-3">
              {anomalies.map((item, index) => (
                <div key={`${item.date}-${index}`} className="rounded-xl p-4 border-l-2" style={{ borderColor: item.severity === 'high' ? '#ef4444' : '#f59e0b', background: 'rgba(255,255,255,0.04)' }}>
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{item.type}</p>
                    <span className="text-[11px]" style={{ color: 'var(--text-faint)' }}>{item.date}</span>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.metric}: {fmt.number(item.value)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
