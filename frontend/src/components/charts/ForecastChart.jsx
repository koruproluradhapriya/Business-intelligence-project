import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
  ResponsiveContainer
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card px-3 py-2 text-xs shadow-xl space-y-1">
      <p className="text-white/50">{label}</p>
      {payload.map((p, i) => p.value != null && (
        <p key={i} style={{ color: p.color }} className="font-semibold">
          {p.name}: ${Number(p.value).toLocaleString()}
        </p>
      ))}
    </div>
  )
}

export default function ForecastChart({ historical = [], forecast = [], splitMonth }) {
  const hist = historical.map(d => ({ month: d.period || d.month, revenue: d.value ?? d.revenue, type: 'historical' }))
  const fore = forecast.map(d => ({ month: d.period || d.month, predicted: d.predicted, upper: d.upper, lower: d.lower, type: 'forecast' }))
  const combined = [...hist, ...fore]
  const splitIndex = hist.length - 1

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={combined} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="histGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="foreGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="month" tick={{ fill: '#555577', fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} tick={{ fill: '#555577', fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        {splitIndex >= 0 && <ReferenceLine x={combined[splitIndex]?.month} stroke="rgba(255,255,255,0.15)" strokeDasharray="4 3" label={{ value: 'Forecast →', fill: '#22d3ee', fontSize: 10, position: 'right' }} />}
        <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#6366f1" strokeWidth={2.5} fill="url(#histGrad)" dot={false} />
        <Area type="monotone" dataKey="upper" name="Upper bound" stroke="none" fill="rgba(34,211,238,0.1)" dot={false} />
        <Area type="monotone" dataKey="lower" name="Lower bound" stroke="none" fill="rgba(34,211,238,0)" dot={false} />
        <Line type="monotone" dataKey="predicted" name="Forecast" stroke="#22d3ee" strokeWidth={2.5} strokeDasharray="6 3" dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
