import { useEffect, useState } from 'react'
import { auditAPI } from '../../services/api'
import { fromNow } from '../../utils/helpers'

const EVENT_CONFIG = {
  user_login:             { dot: 'bg-emerald-400', label: '🟢 Admin Logged In',          desc: (e) => e.metadata?.email || 'Admin session started' },
  user_logout:            { dot: 'bg-slate-400',   label: '⚫ Admin Logged Out',          desc: () => 'Session ended' },
  login_failed:           { dot: 'bg-orange-400',  label: '⚠️ Failed Login Attempt',      desc: (e) => `Email: ${e.metadata?.email || 'unknown'}` },
  session_started:        { dot: 'bg-cyan-400',    label: '▶️ Work Session Started',      desc: (e) => `Session ID: ${e.target_id?.slice(0,8)}...` },
  session_ended:          { dot: 'bg-blue-400',    label: '⏹️ Work Session Ended',        desc: (e) => `Worked ${e.metadata?.work_minutes || 0} min · Break ${e.metadata?.break_minutes || 0} min` },
  session_deleted:        { dot: 'bg-red-400',     label: '🗑️ Session Deleted',           desc: () => 'Session was removed' },
  session_force_ended:    { dot: 'bg-orange-400',  label: '⚡ Session Force Ended',       desc: () => 'Previous session closed automatically' },
  abnormality_detected:   { dot: 'bg-red-400',     label: '🚨 Suspicious Activity',       desc: (e) => `${e.metadata?.type?.replace(/_/g,' ') || 'Unknown'} — ${Math.round((e.metadata?.confidence || 0) * 100)}% confidence` },
  flag_reviewed:          { dot: 'bg-amber-400',   label: '✅ Flag Reviewed by Admin',    desc: (e) => `Decision: ${e.metadata?.decision || 'unknown'} · Severity: ${e.metadata?.severity || '—'}` },
  admin_action:           { dot: 'bg-rose-400',    label: '🛡️ Admin Action Taken',        desc: (e) => e.metadata?.action_type?.replace(/_/g,' ') || 'Action recorded' },
  appeal_submitted:       { dot: 'bg-purple-400',  label: '📩 Employee Filed Appeal',     desc: (e) => e.metadata?.reason_preview || 'Appeal submitted' },
  appeal_reviewed:        { dot: 'bg-pink-400',    label: '📋 Appeal Decision Made',      desc: (e) => `Decision: ${e.metadata?.decision || 'unknown'}` },
  work_rule_created:      { dot: 'bg-cyan-400',    label: '📐 Work Rule Created',         desc: (e) => `Department: ${e.metadata?.department || 'Global'}` },
  work_rule_updated:      { dot: 'bg-cyan-400',    label: '✏️ Work Rule Updated',         desc: (e) => `Department: ${e.metadata?.department || 'Global'}` },
  work_rule_deleted:      { dot: 'bg-red-400',     label: '🗑️ Work Rule Deleted',         desc: (e) => `Department: ${e.metadata?.department || 'Global'}` },
  employee_registered:    { dot: 'bg-emerald-400', label: '👤 New Employee Added',        desc: (e) => e.metadata?.email || 'New account created' },
  password_changed:       { dot: 'bg-amber-400',   label: '🔑 Password Changed',          desc: () => 'Account password updated' },
  prefs_updated:          { dot: 'bg-slate-400',   label: '⚙️ Notification Prefs Changed',desc: () => 'Notification settings updated' },
}

const DEFAULT_CONFIG = {
  dot: 'bg-slate-400',
  label: (type) => type?.replace(/_/g, ' ')?.replace(/\b\w/g, c => c.toUpperCase()) || 'System Event',
  desc: (e) => e.action?.replace(/_/g, ' ') || ''
}

export default function LiveFeed() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchEvents = () => {
    auditAPI.getAll({ limit: 20 })
      .then(r => setEvents(r.data?.logs || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchEvents()
    const interval = setInterval(fetchEvents, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="card p-5 flex flex-col" style={{ maxHeight: '420px' }}>
      <div className="flex items-center justify-between mb-4 shrink-0">
        <h3 className="section-title">Live Feed</h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-mono text-sentinel-muted">LIVE</span>
        </div>
      </div>

      {/* Scrollable area */}
      <div className="overflow-y-auto flex-1 -mx-1 px-1">
        {loading ? (
          Array(6).fill(0).map((_, i) => (
            <div key={i} className="flex gap-3 py-2.5">
              <div className="w-2 h-2 rounded-full bg-navy-700 mt-1.5 shrink-0 animate-pulse" />
              <div className="flex-1">
                <div className="h-3 bg-navy-700 rounded w-3/4 animate-pulse" />
                <div className="h-2 bg-navy-700 rounded w-1/2 mt-1 animate-pulse" />
              </div>
            </div>
          ))
        ) : events.length === 0 ? (
          <p className="text-sentinel-muted text-sm font-mono text-center py-8">No recent activity</p>
        ) : (
          events.map((e, i) => {
            const config = EVENT_CONFIG[e.event_type]
            const label  = config?.label || DEFAULT_CONFIG.label(e.event_type)
            const desc   = config ? config.desc(e) : DEFAULT_CONFIG.desc(e)
            const dot    = config?.dot || DEFAULT_CONFIG.dot

            return (
              <div key={e.id} className="flex gap-3 py-2.5 border-b border-sentinel-border/30 last:border-0">
                <div className={`w-2 h-2 rounded-full ${dot} mt-1.5 shrink-0`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-sentinel-text font-mono font-medium">{label}</p>
                  {desc && (
                    <p className="text-[11px] text-sentinel-muted mt-0.5 truncate font-mono">{desc}</p>
                  )}
                </div>
                <span className="text-[10px] font-mono text-sentinel-muted shrink-0 mt-0.5">{fromNow(e.created_at)}</span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}