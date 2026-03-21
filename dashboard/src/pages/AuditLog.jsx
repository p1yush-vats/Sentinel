import { useEffect, useState } from 'react'
import { auditAPI } from '../services/api'
import { fmt, fromNow } from '../utils/helpers'
import { ScrollText, RefreshCw, X } from 'lucide-react'

// Human-readable labels matching LiveFeed
const EVENT_LABELS = {
  user_login:           { color: 'text-emerald-400', label: 'Admin Logged In',           icon: '🟢' },
  user_logout:          { color: 'text-slate-400',   label: 'Admin Logged Out',           icon: '⚫' },
  login_failed:         { color: 'text-orange-400',  label: 'Failed Login Attempt',       icon: '⚠️' },
  session_started:      { color: 'text-cyan-400',    label: 'Work Session Started',        icon: '▶️' },
  session_ended:        { color: 'text-blue-400',    label: 'Work Session Ended',          icon: '⏹️' },
  session_deleted:      { color: 'text-red-400',     label: 'Session Deleted',             icon: '🗑️' },
  session_force_ended:  { color: 'text-orange-400',  label: 'Session Force Ended',         icon: '⚡' },
  abnormality_detected: { color: 'text-red-400',     label: 'Suspicious Activity Detected',icon: '🚨' },
  flag_reviewed:        { color: 'text-amber-400',   label: 'Flag Reviewed',               icon: '✅' },
  admin_action:         { color: 'text-rose-400',    label: 'Admin Action',                icon: '🛡️' },
  appeal_submitted:     { color: 'text-purple-400',  label: 'Appeal Submitted',            icon: '📩' },
  appeal_reviewed:      { color: 'text-pink-400',    label: 'Appeal Decision Made',        icon: '📋' },
  work_rule_created:    { color: 'text-cyan-400',    label: 'Work Rule Created',           icon: '📐' },
  work_rule_updated:    { color: 'text-cyan-400',    label: 'Work Rule Updated',           icon: '✏️' },
  work_rule_deleted:    { color: 'text-red-400',     label: 'Work Rule Deleted',           icon: '🗑️' },
  employee_registered:  { color: 'text-emerald-400', label: 'New Employee Added',          icon: '👤' },
  password_changed:     { color: 'text-amber-400',   label: 'Password Changed',            icon: '🔑' },
  prefs_updated:        { color: 'text-slate-400',   label: 'Notification Prefs Changed',  icon: '⚙️' },
}

const ALL_EVENT_TYPES = Object.keys(EVENT_LABELS)

// Build a human-readable detail string from metadata
function getDetail(log) {
  const m = log.metadata || {}
  switch (log.event_type) {
    case 'session_ended':
      return `Worked ${m.work_minutes || 0} min · Break ${m.break_minutes || 0} min · Status: ${m.status || '—'}`
    case 'abnormality_detected':
      return `Type: ${m.type?.replace(/_/g,' ') || '—'} · Confidence: ${Math.round((m.confidence || 0) * 100)}% · Severity: ${m.severity || '—'}`
    case 'flag_reviewed':
      return `Decision: ${m.decision || '—'} · Severity: ${m.severity || '—'}`
    case 'login_failed':
      return `Email: ${m.email || '—'}`
    case 'appeal_reviewed':
      return `Decision: ${m.decision || '—'}`
    case 'appeal_submitted':
      return m.reason_preview || '—'
    case 'work_rule_created':
    case 'work_rule_updated':
    case 'work_rule_deleted':
      return `Department: ${m.department || 'Global'} · Sensitivity: ${m.sensitivity || '—'}`
    case 'admin_action':
      return m.action_type?.replace(/_/g,' ') || m.justification?.slice(0,60) || '—'
    case 'employee_registered':
      return `Email: ${m.email || '—'} · Dept: ${m.department || '—'}`
    default:
      return log.action?.replace(/_/g,' ') || '—'
  }
}

export default function AuditLog() {
  const [logs,       setLogs]       = useState([])
  const [loading,    setLoading]    = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [eventType,  setEventType]  = useState('')
  const [dateFrom,   setDateFrom]   = useState('')
  const [dateTo,     setDateTo]     = useState('')

  const load = (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    const params = { limit: 200 }
    if (eventType) params.event_type = eventType
    auditAPI.getAll(params)
      .then(r => setLogs(r.data?.logs || []))
      .catch(() => {})
      .finally(() => { setLoading(false); setRefreshing(false) })
  }

  useEffect(() => { load() }, [eventType])

  const clearFilters = () => { setEventType(''); setDateFrom(''); setDateTo('') }
  const hasFilters = eventType || dateFrom || dateTo

  const filtered = logs.filter(l => {
    if (!l.created_at) return true
    const d = new Date(l.created_at.includes('Z') || l.created_at.includes('+') ? l.created_at : l.created_at + 'Z')
    if (dateFrom && d < new Date(dateFrom)) return false
    if (dateTo) {
      const to = new Date(dateTo)
      to.setDate(to.getDate() + 1)
      if (d > to) return false
    }
    return true
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <h1 className="font-display font-bold text-2xl text-sentinel-text">Audit Log</h1>
          <p className="text-sentinel-muted text-sm font-mono mt-1">{filtered.length} events recorded</p>
        </div>
        <button onClick={() => load(true)} className="btn-ghost flex items-center gap-2">
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="glow-line" />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end animate-fade-in stagger-1">
        <div>
          <p className="label mb-1">Event Type</p>
          <select value={eventType} onChange={e => setEventType(e.target.value)} className="input-field w-auto">
            <option value="">All Events</option>
            {ALL_EVENT_TYPES.map(t => (
              <option key={t} value={t}>
                {EVENT_LABELS[t]?.icon} {EVENT_LABELS[t]?.label || t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <p className="label mb-1">From Date</p>
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="input-field w-auto" />
        </div>
        <div>
          <p className="label mb-1">To Date</p>
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="input-field w-auto" />
        </div>
        {hasFilters && (
          <button onClick={clearFilters} className="btn-ghost flex items-center gap-1.5 text-xs mb-0.5">
            <X size={12} /> Clear
          </button>
        )}
      </div>

      <div className="card overflow-hidden animate-fade-in stagger-2">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sentinel-border">
                <th className="label text-left px-5 py-3">Event</th>
                <th className="label text-left px-5 py-3 hidden md:table-cell">Details</th>
                <th className="label text-left px-5 py-3 hidden lg:table-cell">Actor</th>
                <th className="label text-left px-5 py-3">Time</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array(10).fill(0).map((_, i) => (
                  <tr key={i} className="table-row">
                    <td colSpan={4} className="px-5 py-3">
                      <div className="h-3 bg-navy-700 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-5 py-12 text-center">
                    <p className="text-sentinel-muted font-mono text-sm">No events match your filters</p>
                  </td>
                </tr>
              ) : filtered.map((log, i) => {
                const config = EVENT_LABELS[log.event_type]
                const label  = config ? `${config.icon} ${config.label}` : log.event_type?.replace(/_/g,' ')
                const color  = config?.color || 'text-sentinel-muted'
                const detail = getDetail(log)

                return (
                  <tr key={log.id} className={`table-row animate-fade-in stagger-${Math.min(i % 5 + 1, 5)}`}>
                    <td className="px-5 py-3 min-w-[200px]">
                      <span className={`text-xs font-mono font-medium ${color}`}>{label}</span>
                    </td>
                    <td className="px-5 py-3 hidden md:table-cell max-w-xs">
                      <span className="text-xs font-mono text-sentinel-muted truncate block" title={detail}>
                        {detail}
                      </span>
                    </td>
                    <td className="px-5 py-3 hidden lg:table-cell">
                      <span className="text-xs font-mono text-sentinel-muted">
                        {log.actor_id ? `${log.actor_id.slice(0, 8)}…` : 'System'}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <div>
                        <span className="text-xs font-mono text-sentinel-muted" title={fmt(log.created_at)}>
                          {fromNow(log.created_at)}
                        </span>
                        <p className="text-[10px] font-mono text-sentinel-muted/60 hidden lg:block">
                          {fmt(log.created_at)}
                        </p>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}