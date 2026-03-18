import { useEffect, useState } from 'react'
import { auditAPI } from '../../services/api'
import { fromNow } from '../../utils/helpers'
import { Activity } from 'lucide-react'

const EVENT_STYLES = {
  user_login:          { dot: 'bg-emerald-400', label: 'Login' },
  user_logout:         { dot: 'bg-slate-400',   label: 'Logout' },
  session_started:     { dot: 'bg-cyan-400',    label: 'Session Start' },
  session_ended:       { dot: 'bg-blue-400',    label: 'Session End' },
  abnormality_detected:{ dot: 'bg-red-400',     label: 'Flag Detected' },
  flag_reviewed:       { dot: 'bg-amber-400',   label: 'Flag Reviewed' },
  login_failed:        { dot: 'bg-orange-400',  label: 'Login Failed' },
  appeal_submitted:    { dot: 'bg-purple-400',  label: 'Appeal Filed' },
  appeal_reviewed:     { dot: 'bg-pink-400',    label: 'Appeal Reviewed' },
  admin_action:        { dot: 'bg-rose-400',    label: 'Admin Action' },
}

export default function LiveFeed() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchEvents = () => {
    auditAPI.getAll({ limit: 12 })
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
    <div className="card p-5 h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title">Live Feed</h3>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-mono text-sentinel-muted">LIVE</span>
        </div>
      </div>

      <div className="space-y-0">
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
            const style = EVENT_STYLES[e.event_type] || { dot: 'bg-slate-400', label: e.event_type }
            return (
              <div key={e.id} className={`flex gap-3 py-2.5 border-b border-sentinel-border/30 last:border-0 animate-fade-in stagger-${Math.min(i+1,5)}`}>
                <div className={`w-2 h-2 rounded-full ${style.dot} mt-1.5 shrink-0`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-sentinel-text font-mono">{style.label}</p>
                  <p className="text-[11px] text-sentinel-muted mt-0.5 truncate">{e.action?.replace(/_/g, ' ')}</p>
                </div>
                <span className="text-[10px] font-mono text-sentinel-muted shrink-0">{fromNow(e.created_at)}</span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
