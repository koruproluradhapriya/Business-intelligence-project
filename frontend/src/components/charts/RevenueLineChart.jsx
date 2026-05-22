import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card px-3 py-2 text-xs shadow-xl">
      <p className="text-white/50 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="font-semibold" style={{ color: p.color }}>
          {p.name}: ${Number(p.value).toLocaleString()}
        </p>
      ))}
    </div>
  )
}

export default function RevenueLineChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="month" tick={{ fill: '#555577', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} tick={{ fill: '#555577', fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#6366f1" strokeWidth={2.5} fill="url(#revGrad)" dot={{ r: 3, fill: '#0a0a0f', stroke: '#6366f1', strokeWidth: 2 }} activeDot={{ r: 5 }} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
