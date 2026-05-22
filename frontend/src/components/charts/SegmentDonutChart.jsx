import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="glass-card px-3 py-2 text-xs shadow-xl">
      <p className="text-white font-semibold">{d.segment}</p>
      <p style={{ color: d.color }}>{d.count?.toLocaleString()} customers</p>
    </div>
  )
}

export default function SegmentDonutChart({ data = [] }) {
  const total = data.reduce((s, d) => s + (d.count || 0), 0)
  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="segment" cx="50%" cy="50%"
            innerRadius={55} outerRadius={80} strokeWidth={0} paddingAngle={3}>
            {data.map((d, i) => <Cell key={i} fill={d.color} />)}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-white font-bold text-xl">{total.toLocaleString()}</span>
        <span className="text-white/30 text-xs">Customers</span>
      </div>
    </div>
  )
}
