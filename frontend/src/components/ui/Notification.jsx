import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react'

const ICONS = { success: CheckCircle, error: XCircle, warning: AlertCircle, info: Info }
const COLORS = {
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  error: 'border-red-500/30 bg-red-500/10 text-red-300',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  info: 'border-brand-500/30 bg-brand-500/10 text-brand-300',
}

export default function Notification({ id, message, type = 'info', onDismiss }) {
  const Icon = ICONS[type] || Info
  return (
    <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 50 }}
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm text-sm font-medium max-w-xs shadow-xl ${COLORS[type]}`}>
      <Icon size={16} className="flex-shrink-0 mt-0.5" />
      <span className="flex-1">{message}</span>
      <button onClick={() => onDismiss(id)} className="opacity-60 hover:opacity-100 transition-opacity">
        <X size={14} />
      </button>
    </motion.div>
  )
}
