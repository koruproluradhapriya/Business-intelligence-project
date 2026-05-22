export const fmt = {
  currency: (v) => {
    if (v == null || isNaN(v)) return '$0'
    const n = Number(v)
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}k`
    return `$${n.toLocaleString()}`
  },
  number: (v) => {
    if (v == null || isNaN(v)) return '0'
    return Number(v).toLocaleString()
  },
  percent: (v) => `${v >= 0 ? '+' : ''}${Number(v).toFixed(1)}%`,
  metric: (value, format = 'number') => {
    if (format === 'currency') return fmt.currency(value)
    if (format === 'percent') return fmt.percent(value || 0)
    if (format === 'percent_whole') return `${Number(value || 0).toFixed(0)}%`
    return fmt.number(value)
  },
  date: (d) => d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '',
}
