import { useEffect, useState } from 'react'
import { auditAPI } from '../services/api'
import { fmt, fromNow } from '../utils/helpers'
import { ScrollText, RefreshCw } from 'lucide-react'

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

export default function AuditLog() {
  const [logs,       setLogs]       = useState([])
  const [loading,    setLoading]    = useState(true)
  const [eventType,  setEventType]  = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const load = (showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    const params = { limit: 150 }
    if (eventType) params.event_type = eventType
    auditAPI.getAll(params)
      .then(r => setLogs(r.data?.logs || []))
      .catch(() => {})
      .finally(() => { setLoading(false); setRefreshing(false) })
  }

  useEffect(() => { load() }, [eventType])

  const EVENT_TYPES = [...new Set(logs.map(l => l.event_type))]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <h1 className="font-display font-bold text-2xl text-sentinel-text">Audit Log</h1>
          <p className="text-sentinel-muted text-sm font-mono mt-1">{logs.length} entries</p>
        </div>
        <button onClick={() => load(true)} className="btn-ghost flex items-center gap-2">
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="glow-line" />

      <div className="flex gap-3 flex-wrap animate-fade-in stagger-1">
        <select value={eventType} onChange={e => setEventType(e.target.value)} className="input-field w-auto">
          <option value="">All Events</option>
          {EVENT_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
        </select>
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
              ) : logs.map((log, i) => (
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
                    <span className="text-xs font-mono text-sentinel-muted">{log.actor_id?.slice(0, 8) || '—'}…</span>
                  </td>
                  <td className="px-5 py-3 hidden lg:table-cell">
                    <span className="text-xs font-mono text-sentinel-muted">{log.target_type || '—'}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-mono text-sentinel-muted" title={fmt(log.created_at)}>{fromNow(log.created_at)}</span>
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
