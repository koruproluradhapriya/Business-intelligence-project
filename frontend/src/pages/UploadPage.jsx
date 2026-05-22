import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { uploadApi } from '../api/upload'
import { useApp } from '../context/AppContext'
import {
  ArrowRight, CheckCircle, Database, FileText, Loader2, Trash2, Upload,
} from 'lucide-react'

export default function UploadPage() {
  const { notify, triggerDataRefresh } = useApp()
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)

  const onDrop = useCallback(accepted => {
    if (accepted[0]) {
      setFile(accepted[0])
      setStatus('idle')
      setResult(null)
      setProgress(0)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'text/tab-separated-values': ['.tsv'],
      'application/json': ['.json'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/octet-stream': ['.parquet'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
    onDropRejected: files => notify(files[0]?.errors[0]?.message || 'File rejected', 'error'),
  })

  const handleUpload = async () => {
    if (!file) return
    setStatus('uploading')
    setProgress(0)
    try {
      const res = await uploadApi.uploadFile(file, 'auto', setProgress)
      setResult(res.data)
      setStatus('success')
      triggerDataRefresh()
      notify(`${file.name} processed successfully. Universal dashboard updated.`, 'success')
    } catch (err) {
      setStatus('idle')
      notify(err.response?.data?.error || 'Upload failed. Please inspect the dataset and try again.', 'error')
    }
  }

  const reset = () => {
    setFile(null)
    setStatus('idle')
    setResult(null)
    setProgress(0)
  }

  return (
    <div className="p-7 max-w-5xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h2 style={{ color: 'var(--text-primary)' }} className="font-bold text-2xl">Universal Dataset Intake</h2>
        <p style={{ color: 'var(--text-muted)' }} className="text-sm mt-1">
          Upload CSV, XLSX, XLS, JSON, TSV, or Parquet files. The platform will infer schema, clean the data, and build an adaptive AI-ready dashboard automatically.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 glass-card p-6">
          <div
            {...getRootProps()}
            className={`flex flex-col items-center justify-center gap-4 cursor-pointer transition-all border-2 border-dashed rounded-2xl p-14
              ${isDragActive ? 'border-brand-500 bg-brand-500/10' : 'border-white/[0.08] hover:border-white/20'}`}>
            <input {...getInputProps()} />
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all ${isDragActive ? 'bg-brand-500/20' : 'bg-white/[0.05]'}`}>
              <Upload size={28} style={{ color: isDragActive ? '#6366f1' : 'var(--text-faint)' }} />
            </div>
            {file ? (
              <div className="text-center">
                <div className="flex items-center gap-2 justify-center mb-1">
                  <FileText size={16} style={{ color: '#6366f1' }} />
                  <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{file.name}</span>
                </div>
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{(file.size / 1024).toFixed(1)} KB</span>
              </div>
            ) : (
              <div className="text-center">
                <p className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>
                  {isDragActive ? 'Drop the dataset here' : 'Drop any structured dataset here or click to browse'}
                </p>
                <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>No predefined schema required</p>
              </div>
            )}
          </div>

          {file && status !== 'success' && (
            <div className="flex gap-3 mt-4">
              <button onClick={handleUpload} disabled={status === 'uploading'} className="btn-primary flex-1 py-3 flex items-center justify-center gap-2 text-sm">
                {status === 'uploading' ? <><Loader2 size={16} className="animate-spin" />Processing… {progress}%</> : 'Upload & Analyze'}
              </button>
              <button onClick={reset} className="btn-secondary px-4" title="Clear">
                <Trash2 size={16} />
              </button>
            </div>
          )}

          <AnimatePresence>
            {status === 'uploading' && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mt-4">
                <div className="flex justify-between text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                  <span>Analyzing {file?.name}</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                  <motion.div className="h-full rounded-full" style={{ background: 'linear-gradient(90deg,#2563eb,#14b8a6)' }} initial={{ width: 0 }} animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }} />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Database size={16} style={{ color: '#22d3ee' }} />
            <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>What Happens After Upload</h3>
          </div>
          <div className="space-y-3 text-sm" style={{ color: 'var(--text-muted)' }}>
            <p>1. File type detection and dynamic parsing</p>
            <p>2. Column normalization and semantic inference</p>
            <p>3. Missing value, duplicate, type, and outlier profiling</p>
            <p>4. Automatic charts, insights, forecast, and recommendations</p>
            <p>5. Chat-ready dataset context for business Q&amp;A</p>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {status === 'success' && result && (
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 flex items-center justify-center">
                <CheckCircle size={20} className="text-emerald-400" />
              </div>
              <div>
                <h3 className="font-bold" style={{ color: 'var(--text-primary)' }}>Dataset Processed Successfully</h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>The intelligence engine profiled your dataset and refreshed the dashboard.</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                ['Rows', result.rowCount?.toLocaleString()],
                ['Columns', result.columns?.length],
                ['Schema', result.schema],
                ['Duplicates Removed', result.qualityReport?.duplicateRowsRemoved || 0],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>{label}</p>
                  <p className="font-bold capitalize" style={{ color: 'var(--text-primary)' }}>{value}</p>
                </div>
              ))}
            </div>

            {result.columnProfiles?.length > 0 && (
              <div>
                <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>Detected Columns</p>
                <div className="flex flex-wrap gap-2">
                  {result.columnProfiles.slice(0, 16).map(col => (
                    <span key={col.name} className="px-3 py-1 rounded-full text-xs" style={{ background: 'rgba(37,99,235,0.12)', color: '#bfdbfe' }}>
                      {col.name} · {col.detectedType}{col.semanticLabel ? ` · ${col.semanticLabel}` : ''}{col.semanticConfidence ? ` · ${Math.round(col.semanticConfidence * 100)}%` : ''}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {!!Object.keys(result.semanticGroups || {}).length && (
              <div>
                <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>Semantic Mapping</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(result.semanticGroups).slice(0, 8).map(([label, columns]) => (
                    <div key={label} className="rounded-xl p-3" style={{ background: 'rgba(255,255,255,0.04)' }}>
                      <p className="text-[11px] uppercase tracking-[0.15em] mb-1" style={{ color: 'var(--text-faint)' }}>{label}</p>
                      <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{columns.join(', ')}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.profileReport && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>Numeric Columns</p>
                  <p className="font-bold" style={{ color: 'var(--text-primary)' }}>{result.profileReport.numericColumns?.length || 0}</p>
                </div>
                <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>Categorical Columns</p>
                  <p className="font-bold" style={{ color: 'var(--text-primary)' }}>{result.profileReport.categoricalColumns?.length || 0}</p>
                </div>
                <div className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-faint)' }}>Datetime Columns</p>
                  <p className="font-bold" style={{ color: 'var(--text-primary)' }}>{result.profileReport.datetimeColumns?.length || 0}</p>
                </div>
              </div>
            )}

            {result.preview?.length > 0 && (
              <div>
                <p className="text-xs mb-2" style={{ color: 'var(--text-faint)' }}>Preview</p>
                <div className="overflow-x-auto rounded-xl border" style={{ borderColor: 'var(--border-color)' }}>
                  <table className="w-full text-xs">
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                        {Object.keys(result.preview[0]).map(key => (
                          <th key={key} className="text-left px-3 py-2 font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: 'var(--text-faint)' }}>{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.preview.slice(0, 5).map((row, index) => (
                        <tr key={index} style={{ borderTop: '1px solid var(--border-color)' }}>
                          {Object.values(row).map((value, cellIndex) => (
                            <td key={cellIndex} className="px-3 py-2 whitespace-nowrap" style={{ color: 'var(--text-muted)' }}>
                              {String(value ?? '').slice(0, 28)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button onClick={() => navigate('/')} className="btn-primary flex items-center gap-2 flex-1 justify-center py-2.5">
                Open Dashboard <ArrowRight size={15} />
              </button>
              <button onClick={reset} className="btn-secondary px-4 py-2.5 text-sm">
                Upload Another
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
