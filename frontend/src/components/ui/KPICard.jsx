import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { SparkLineChart } from './SparkLine'

export default function KPICard({ title, value, change, icon: Icon, color = '#6366f1', sparkData, loading }) {
  const positive = change >= 0

  if (loading) return (
    <div className="glass-card p-5 animate-pulse">
      <div className="h-10 w-10 bg-white/10 rounded-xl mb-3" />
      <div className="h-3 w-20 bg-white/10 rounded mb-2" />
      <div className="h-7 w-28 bg-white/10 rounded mb-2" />
      <div className="h-3 w-16 bg-white/10 rounded" />
    </div>
  )

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      className="glass-card p-5 hover:border-white/[0.14] transition-all duration-200 cursor-default group">
      <div className="flex justify-between items-start mb-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
          style={{ background: `${color}22` }}>
          <Icon size={20} style={{ color }} />
        </div>
        {sparkData && <SparkLineChart data={sparkData} color={color} />}
      </div>
      <p className="text-white/40 text-[11px] font-medium uppercase tracking-widest mb-1">{title}</p>
      <p className="text-white text-2xl font-bold tracking-tight mb-1.5">{value}</p>
      {change !== undefined && (
        <div className={`flex items-center gap-1 text-xs font-semibold ${positive ? 'text-emerald-400' : 'text-red-400'}`}>
          {positive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {Math.abs(change)}% vs last period
        </div>
      )}
    </motion.div>
  )
}
