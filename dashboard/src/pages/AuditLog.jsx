import { useEffect, useState } from 'react'
import { auditAPI } from '../services/api'
import { fmt, fromNow } from '../utils/helpers'
import { ScrollText, RefreshCw, X } from 'lucide-react'

const EVENT_COLORS = {
  user_login:           'text-emerald-400',
  user_logout:          'text-slate-400',
  login_failed:         'text-orange-400',
  session_started:      'text-cyan-400',
  session_ended:        'text-blue-400',
  session_deleted:      'text-red-400',
  session_force_ended:  'text-orange-400',
  abnormality_detected: 'text-red-400',
  flag_reviewed:        'text-amber-400',
  admin_action:         'text-rose-400',
  appeal_submitted:     'text-purple-400',
  appeal_reviewed:      'text-pink-400',
  work_rule_created:    'text-cyan-400',
  work_rule_updated:    'text-cyan-400',
  work_rule_deleted:    'text-red-400',
  employee_registered:  'text-emerald-400',
  password_changed:     'text-amber-400',
  prefs_updated:        'text-slate-400',
}

// All known event types so filter isn't limited to what's in current page
const ALL_EVENT_TYPES = Object.keys(EVENT_COLORS)

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

  const clearFilters = () => {
    setEventType('')
    setDateFrom('')
    setDateTo('')
  }

  const hasFilters = eventType || dateFrom || dateTo

  // Client-side date filter (backend doesn't support date range on audit)
  const filtered = logs.filter(l => {
    if (!l.created_at) return true
    const d = new Date(l.created_at.includes('Z') || l.created_at.includes('+') ? l.created_at : l.created_at + 'Z')
    if (dateFrom) {
      const from = new Date(dateFrom)
      if (d < from) return false
    }
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
          <p className="text-sentinel-muted text-sm font-mono mt-1">{filtered.length} entries</p>
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
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
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
                <th className="label text-left px-5 py-3">Action</th>
                <th className="label text-left px-5 py-3 hidden md:table-cell">Actor</th>
                <th className="label text-left px-5 py-3 hidden lg:table-cell">Target</th>
                <th className="label text-left px-5 py-3">Time</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array(10).fill(0).map((_, i) => (
                  <tr key={i} className="table-row">
                    <td colSpan={5} className="px-5 py-3">
                      <div className="h-3 bg-navy-700 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-12 text-center">
                    <p className="text-sentinel-muted font-mono text-sm">No events match your filters</p>
                  </td>
                </tr>
              ) : filtered.map((log, i) => (
                <tr key={log.id} className={`table-row animate-fade-in stagger-${Math.min(i % 5 + 1, 5)}`}>
                  <td className="px-5 py-3">
                    <span className={`text-xs font-mono ${EVENT_COLORS[log.event_type] || 'text-sentinel-muted'}`}>
                      {log.event_type?.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-mono text-sentinel-text">{log.action?.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="px-5 py-3 hidden md:table-cell">
                    <span className="text-xs font-mono text-sentinel-muted">
                      {log.actor_id ? `${log.actor_id.slice(0, 8)}…` : '—'}
                    </span>
                  </td>
                  <td className="px-5 py-3 hidden lg:table-cell">
                    <span className="text-xs font-mono text-sentinel-muted">{log.target_type || '—'}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-mono text-sentinel-muted" title={fmt(log.created_at)}>
                      {fromNow(log.created_at)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}