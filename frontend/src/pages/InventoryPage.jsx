import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { inventoryApi } from '../api/inventory'
import { useApp } from '../context/AppContext'
import { AlertTriangle, CheckCircle, XCircle, Package } from 'lucide-react'

const STATUS_CONFIG = {
  critical: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-500/30', label: 'Critical' },
  warning: { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-500/30', label: 'Warning' },
  healthy: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-500/30', label: 'Healthy' },
  overstock: { icon: Package, color: 'text-cyan-400', bg: 'bg-cyan-400/10', border: 'border-cyan-500/30', label: 'Overstock' },
}

export default function InventoryPage() {
  const { notify } = useApp()
  const [data, setData] = useState(null)
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    inventoryApi.getStatus()
      .then(res => setData(res.data))
      .catch(() => notify('Failed to load inventory', 'error'))
      .finally(() => setLoading(false))
  }, [])

  const summary = data?.summary || {}
  const items = (data?.items || []).filter(i => filter === 'all' || i.status === filter)

  return (
    <div className="p-7 space-y-6 animate-fade-in">
      <div className="grid grid-cols-4 gap-4">
        {[
          { key: 'critical', label: 'Critical', icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10' },
          { key: 'warning', label: 'Warning', icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
          { key: 'healthy', label: 'Healthy', icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
          { key: 'overstock', label: 'Overstock', icon: Package, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
        ].map(({ key, label, icon: Icon, color, bg }) => (
          <motion.div key={key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            onClick={() => setFilter(filter === key ? 'all' : key)}
            className={`glass-card p-5 flex items-center gap-4 cursor-pointer hover:border-white/[0.14] transition-all ${filter === key ? 'border-brand-500/40' : ''}`}>
            <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center`}>
              <Icon size={20} className={color} />
            </div>
            <div>
              <p className="text-white/40 text-xs">{label}</p>
              <p className={`font-bold text-2xl ${color}`}>{loading ? '—' : summary[key] ?? 0}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6">
        <div className="flex justify-between items-center mb-5">
          <h3 className="text-white font-semibold text-sm">Inventory Status</h3>
          <span className="text-white/30 text-xs">{items.length} items {filter !== 'all' ? `(${filter})` : ''}</span>
        </div>
        <div className="space-y-3">
          {items.map((item, i) => {
            const cfg = STATUS_CONFIG[item.status] || STATUS_CONFIG.healthy
            const Icon = cfg.icon
            return (
              <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                className={`flex items-start gap-4 p-4 rounded-xl border ${cfg.bg} ${cfg.border}`}>
                <Icon size={18} className={`flex-shrink-0 mt-0.5 ${cfg.color}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-white font-semibold text-sm">{item.product}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color}`}>{cfg.label}</span>
                  </div>
                  <div className="flex gap-4 text-xs text-white/40 mb-2">
                    <span>Stock: <strong className="text-white/70">{item.stock}</strong></span>
                    <span>Reorder at: <strong className="text-white/70">{item.reorderLevel}</strong></span>
                    <span>Daily sales: <strong className="text-white/70">{item.avgDailySales}</strong></span>
                    {item.daysToStockout != null && <span>Days left: <strong className={cfg.color}>{item.daysToStockout}</strong></span>}
                  </div>
                  <p className="text-white/40 text-xs">{item.recommendation}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </motion.div>
    </div>
  )
}
