import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { flagsAPI, employeesAPI } from '../services/api'
import { fromNow, severityBadge, initials, deptColor } from '../utils/helpers'
import { AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Flags() {
  const navigate = useNavigate()
  const [flags,         setFlags]         = useState([])
  const [employees,     setEmployees]     = useState({})   // id → employee map
  const [loading,       setLoading]       = useState(true)
  const [expanded,      setExpanded]      = useState(null)
  const [decision,      setDecision]      = useState('')
  const [justification, setJustification] = useState('')
  const [reviewing,     setReviewing]     = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([
      flagsAPI.getUnreviewed({ limit: 100 }),
      employeesAPI.getAll({ limit: 500 }),
    ])
      .then(([flagRes, empRes]) => {
        setFlags(flagRes.data?.abnormalities || [])
        const map = {}
        ;(empRes.data?.employees || []).forEach(e => { map[e.id] = e })
        setEmployees(map)
      })
      .catch(() => toast.error('Failed to load flags'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleReview = async (flag) => {
    if (!decision)            { toast.error('Select a decision'); return }
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
    { value: 'dismissed',      label: 'Dismiss',  icon: XCircle,       color: 'text-slate-400' },
    { value: 'warning_issued', label: 'Warn',      icon: AlertTriangle, color: 'text-amber-400' },
    { value: 'escalated',      label: 'Escalate',  icon: CheckCircle,   color: 'text-red-400'   },
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
            const emp        = employees[flag.employee_id]
            const color      = deptColor(emp?.department)
            const detections = flag.detections || {}
            const types      = Object.keys(detections)
            const isExpanded = expanded === flag.id

            return (
              <div key={flag.id}
                className={`card overflow-hidden transition-all duration-300 animate-fade-in stagger-${Math.min(i+1,5)}
                  ${isExpanded ? 'border-red-400/20' : ''}`}>

                {/* Header row */}
                <div className="flex items-center gap-4 p-5">
                  {/* Employee avatar — clickable */}
                  {emp?.avatar_url ? (
                    <img
                      src={emp.avatar_url}
                      alt={emp.full_name}
                      onClick={() => navigate(`/employees/${emp.id}`)}
                      className="w-9 h-9 rounded-full object-cover shrink-0 cursor-pointer hover:opacity-80 transition-opacity border"
                      style={{ borderColor: color + '50' }}
                      onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
                    />
                  ) : null}
                  <div
                    onClick={() => emp && navigate(`/employees/${emp.id}`)}
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0
                      ${emp ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}
                      ${emp?.avatar_url ? 'hidden' : ''}`}
                    style={{ backgroundColor: color + '18', color, border: `1.5px solid ${color}40` }}
                    title={emp?.full_name || 'Unknown employee'}
                  >
                    {emp ? initials(emp.full_name) : '??'}
                  </div>

                  {/* Main info — click to expand */}
                  <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setExpanded(isExpanded ? null : flag.id)}>
                    {/* Employee name */}
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {emp ? (
                        <span className="text-sm font-medium text-sentinel-text">{emp.full_name}</span>
                      ) : (
                        <span className="text-sm font-mono text-sentinel-muted">Unknown employee</span>
                      )}
                      {emp?.department && (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ backgroundColor: color + '18', color }}>
                          {emp.department}
                        </span>
                      )}
                    </div>
                    {/* Badges */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={severityBadge(flag.overall_severity)}>{flag.overall_severity}</span>
                      {types.slice(0, 2).map(t => (
                        <span key={t} className="badge-medium">{t.replace(/_/g, ' ')}</span>
                      ))}
                      {types.length > 2 && (
                        <span className="text-xs font-mono text-sentinel-muted">+{types.length - 2} more</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      <span className="text-xs font-mono text-sentinel-muted">
                        Confidence: {Math.round((flag.confidence_score || 0) * 100)}%
                      </span>
                      <span className="text-xs font-mono text-sentinel-muted">
                        {fromNow(flag.first_detected_at)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {/* Link to employee */}
                    {emp && (
                      <button
                        onClick={() => navigate(`/employees/${emp.id}`)}
                        className="w-7 h-7 rounded-lg hover:bg-navy-700 flex items-center justify-center text-sentinel-muted hover:text-cyan-400 transition-colors"
                        title="View employee"
                      >
                        <ExternalLink size={13} />
                      </button>
                    )}
                    <button onClick={() => setExpanded(isExpanded ? null : flag.id)}>
                      {isExpanded
                        ? <ChevronUp size={16} className="text-sentinel-muted" />
                        : <ChevronDown size={16} className="text-sentinel-muted" />}
                    </button>
                  </div>
                </div>

                {/* Expanded panel */}
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
                      <div className="flex gap-2 mb-3 flex-wrap">
                        {DECISIONS.map(({ value, label, icon: Icon, color: c }) => (
                          <button key={value} onClick={() => setDecision(value)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-mono border transition-all
                              ${decision === value ? 'bg-navy-700 border-cyan-400/30 text-cyan-400' : 'border-sentinel-border text-sentinel-muted hover:text-sentinel-text'}`}>
                            <Icon size={13} className={decision === value ? 'text-cyan-400' : c} />
                            {label}
                          </button>
                        ))}
                      </div>
                      <textarea
                        value={justification}
                        onChange={e => setJustification(e.target.value)}
                        placeholder="Justification for this decision…"
                        rows={2}
                        className="input-field resize-none mb-3"
                      />
                      <button
                        onClick={() => handleReview(flag)}
                        disabled={reviewing === flag.id}
                        className="btn-primary disabled:opacity-50"
                      >
                        {reviewing === flag.id ? 'Submitting…' : 'Submit Review'}
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