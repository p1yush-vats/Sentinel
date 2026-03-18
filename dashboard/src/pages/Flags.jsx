import { useEffect, useState } from 'react'
import { flagsAPI } from '../services/api'
import { fromNow, severityBadge, initials } from '../utils/helpers'
import { AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Flags() {
  const [flags,    setFlags]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [decision, setDecision] = useState('')
  const [justification, setJustification] = useState('')
  const [reviewing, setReviewing] = useState(null)

  const load = () => {
    flagsAPI.getUnreviewed({ limit: 100 })
      .then(r => setFlags(r.data?.abnormalities || []))
      .catch(() => toast.error('Failed to load flags'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleReview = async (flag) => {
    if (!decision) { toast.error('Select a decision'); return }
    if (!justification.trim()) { toast.error('Add justification'); return }
    setReviewing(flag.id)
    try {
      await flagsAPI.review(flag.id, { decision, justification })
      toast.success('Flag reviewed')
      setFlags(prev => prev.filter(f => f.id !== flag.id))
      setExpanded(null)
      setDecision('')
      setJustification('')
    } catch { toast.error('Review failed') }
    finally { setReviewing(null) }
  }

  const DECISIONS = [
    { value: 'dismissed',      label: 'Dismiss',    icon: XCircle,     color: 'text-slate-400' },
    { value: 'warning_issued', label: 'Warn',        icon: AlertTriangle, color: 'text-amber-400' },
    { value: 'escalated',      label: 'Escalate',    icon: CheckCircle, color: 'text-red-400' },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <h1 className="font-display font-bold text-2xl text-sentinel-text">Flags</h1>
          <p className="text-sentinel-muted text-sm font-mono mt-1">{flags.length} pending review</p>
        </div>
        {flags.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
            <span className="text-xs font-mono text-red-400">{flags.length} UNREVIEWED</span>
          </div>
        )}
      </div>

      <div className="glow-line" />

      {loading ? (
        Array(4).fill(0).map((_, i) => (
          <div key={i} className="card p-5">
            <div className="h-4 bg-navy-700 rounded animate-pulse w-1/2 mb-2" />
            <div className="h-3 bg-navy-700 rounded animate-pulse w-1/3" />
          </div>
        ))
      ) : flags.length === 0 ? (
        <div className="card p-12 text-center">
          <CheckCircle size={32} className="text-emerald-400 mx-auto mb-3" />
          <p className="font-display font-semibold text-sentinel-text">All clear</p>
          <p className="text-sentinel-muted text-sm font-mono mt-1">No pending flags</p>
        </div>
      ) : (
        <div className="space-y-3">
          {flags.map((flag, i) => {
            const detections = flag.detections || {}
            const types = Object.keys(detections)
            const isExpanded = expanded === flag.id

            return (
              <div key={flag.id} className={`card overflow-hidden transition-all duration-300 animate-fade-in stagger-${Math.min(i+1,5)} ${isExpanded ? 'border-red-400/20' : ''}`}>
                {/* Header */}
                <div className="flex items-center gap-4 p-5 cursor-pointer" onClick={() => setExpanded(isExpanded ? null : flag.id)}>
                  <div className="w-9 h-9 rounded-full bg-red-400/10 border border-red-400/20 flex items-center justify-center shrink-0">
                    <AlertTriangle size={15} className="text-red-400" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={severityBadge(flag.overall_severity)}>{flag.overall_severity}</span>
                      {types.slice(0, 3).map(t => (
                        <span key={t} className="badge-medium">{t.replace(/_/g, ' ')}</span>
                      ))}
                      {types.length > 3 && <span className="text-xs font-mono text-sentinel-muted">+{types.length - 3} more</span>}
                    </div>
                    <div className="flex items-center gap-3 mt-1.5">
                      <span className="text-xs font-mono text-sentinel-muted">Session: {flag.session_id?.slice(0, 8)}…</span>
                      <span className="text-xs font-mono text-sentinel-muted">Confidence: {Math.round((flag.confidence_score || 0) * 100)}%</span>
                      <span className="text-xs font-mono text-sentinel-muted">{fromNow(flag.first_detected_at)}</span>
                    </div>
                  </div>

                  {isExpanded ? <ChevronUp size={16} className="text-sentinel-muted shrink-0" /> : <ChevronDown size={16} className="text-sentinel-muted shrink-0" />}
                </div>

                {/* Expanded */}
                {isExpanded && (
                  <div className="border-t border-sentinel-border px-5 pb-5 pt-4 space-y-4 animate-fade-in">
                    {/* Detections breakdown */}
                    <div>
                      <p className="label mb-3">Detection Breakdown</p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {types.map(t => {
                          const d = detections[t]
                          return (
                            <div key={t} className="bg-navy-900 rounded-lg px-3 py-2.5 border border-sentinel-border">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-mono text-sentinel-text">{t.replace(/_/g, ' ')}</span>
                                <span className={severityBadge(d.severity)}>{d.severity}</span>
                              </div>
                              <div className="flex gap-4 mt-1.5">
                                <span className="text-xs font-mono text-sentinel-muted">×{d.occurrences} occurrences</span>
                                <span className="text-xs font-mono text-sentinel-muted">{Math.round((d.confidence || 0) * 100)}% confidence</span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    {/* Review panel */}
                    <div className="border-t border-sentinel-border pt-4">
                      <p className="label mb-3">Admin Decision</p>
                      <div className="flex gap-2 mb-3">
                        {DECISIONS.map(({ value, label, icon: Icon, color }) => (
                          <button key={value} onClick={() => setDecision(value)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-mono border transition-all duration-200
                              ${decision === value ? 'bg-navy-700 border-cyan-400/30 text-cyan-400' : 'border-sentinel-border text-sentinel-muted hover:text-sentinel-text'}`}>
                            <Icon size={13} className={decision === value ? 'text-cyan-400' : color} />
                            {label}
                          </button>
                        ))}
                      </div>
                      <textarea
                        value={justification}
                        onChange={e => setJustification(e.target.value)}
                        placeholder="Justification for this decision..."
                        rows={2}
                        className="input-field resize-none mb-3"
                      />
                      <button
                        onClick={() => handleReview(flag)}
                        disabled={reviewing === flag.id}
                        className="btn-primary disabled:opacity-50"
                      >
                        {reviewing === flag.id ? 'Submitting...' : 'Submit Review'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
