import { useState } from 'react'
import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useApp } from '../context/AppContext'
import { authApi } from '../api/auth'
import { User, Bell, Key, CreditCard, Loader2, Check } from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()
  const { notify, theme, toggleTheme } = useApp()
  const [form, setForm] = useState({ name: user?.name || '', businessName: user?.businessName || '' })
  const [settings, setSettings] = useState({ notifications: { email: false, product: true } })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    authApi.getSettings()
      .then(res => setSettings(res.data.settings || { notifications: { email: false, product: true } }))
      .catch(() => notify('Failed to load settings', 'error'))
  }, [])

  const saveProfile = async () => {
    setSaving(true)
    try {
      await authApi.updateProfile(form)
      await authApi.updateSettings({ theme, notifications: settings.notifications })
      setSaved(true)
      notify('Profile saved!', 'success')
      setTimeout(() => setSaved(false), 3000)
    } catch {
      notify('Failed to save profile', 'error')
    } finally { setSaving(false) }
  }

  const sections = [
    {
      title: 'Account', icon: User,
      content: (
        <div className="space-y-4">
          {[['Full Name', 'name', 'John Doe'], ['Business Name', 'businessName', 'Acme Corp'], ['Email', 'email', user?.email || '']].map(([label, key, placeholder]) => (
            <div key={key}>
              <label className="label">{label}</label>
              <input value={key === 'email' ? (user?.email || '') : form[key] || ''} readOnly={key === 'email'}
                onChange={e => key !== 'email' && setForm(f => ({ ...f, [key]: e.target.value }))}
                placeholder={placeholder} className={`input-field ${key === 'email' ? 'opacity-50 cursor-not-allowed' : ''}`} />
            </div>
          ))}
          <button onClick={saveProfile} disabled={saving} className="btn-primary flex items-center gap-2">
            {saving ? <Loader2 size={14} className="animate-spin" /> : saved ? <Check size={14} /> : null}
            {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      )
    },
    {
      title: 'Appearance', icon: Bell,
      content: (
          <div className="flex items-center justify-between">
            <div><p className="text-white text-sm font-medium">Theme</p><p className="text-white/40 text-xs mt-0.5">Switch between dark and light mode</p></div>
          <button onClick={() => {
            toggleTheme()
            authApi.updateSettings({ theme: theme === 'dark' ? 'light' : 'dark', notifications: settings.notifications }).catch(() => {})
          }} className="btn-secondary capitalize">{theme === 'dark' ? '☀️ Light' : '🌙 Dark'}</button>
        </div>
      )
    },
    {
      title: 'API Keys', icon: Key,
      content: (
        <div className="space-y-3">
          <div className="flex items-center justify-between bg-white/[0.04] rounded-xl px-4 py-3">
            <code className="text-white/40 text-xs font-mono">iq_live_sk_••••••••••••••••3j8f</code>
            <button className="text-brand-400 text-xs hover:text-white transition-colors">Copy</button>
          </div>
          <button className="btn-secondary text-xs">+ Generate New Key</button>
        </div>
      )
    },
    {
      title: 'Billing', icon: CreditCard,
      content: (
        <div className="flex items-center justify-between">
          <div><p className="text-white text-sm font-medium">Free Plan</p><p className="text-white/40 text-xs mt-0.5">5 datasets · Basic analytics · PDF reports</p></div>
          <button className="btn-primary text-xs">Upgrade to Pro</button>
        </div>
      )
    },
  ]

  return (
    <div className="p-7 max-w-2xl space-y-4 animate-fade-in">
      {sections.map(({ title, icon: Icon, content }, i) => (
        <motion.div key={title} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
          className="glass-card p-6">
          <div className="flex items-center gap-2.5 mb-5">
            <Icon size={17} className="text-brand-400" />
            <h3 className="text-white font-semibold text-sm">{title}</h3>
          </div>
          {content}
        </motion.div>
      ))}
    </div>
  )
}
