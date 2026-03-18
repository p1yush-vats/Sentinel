import { useEffect, useState } from 'react'
import { sessionsAPI } from '../services/api'
import { fmt, fmtMins, statusBadge, initials } from '../utils/helpers'
import { Search, Clock } from 'lucide-react'

export default function Sessions() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading]   = useState(true)
  const [status, setStatus]     = useState('all')
  const [search, setSearch]     = useState('')

  useEffect(() => {
    const params = { limit: 100 }
    if (status !== 'all') params.status = status
    sessionsAPI.getAll(params)
      .then(r => setSessions(r.data?.sessions || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [status])

  const filtered = search
    ? sessions.filter(s => s.employee_id?.includes(search) || s.id?.includes(search))
    : sessions

  const STATUSES = ['all', 'active', 'completed', 'flagged', 'partial', 'abandoned']

  return (
    <div className="space-y-5">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Sessions</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">{filtered.length} sessions</p>
      </div>

      <div className="glow-line" />

      <div className="flex flex-wrap gap-3 animate-fade-in stagger-1">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-sentinel-muted" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by ID..." className="input-field pl-9" />
        </div>
        <div className="flex gap-2 flex-wrap">
          {STATUSES.map(s => (
            <button key={s} onClick={() => setStatus(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all duration-200 ${status === s ? 'bg-cyan-400/10 text-cyan-400 border border-cyan-400/20' : 'text-sentinel-muted border border-sentinel-border hover:text-sentinel-text'}`}>
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="card overflow-hidden animate-fade-in stagger-2">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sentinel-border">
                <th className="label text-left px-5 py-3">Session ID</th>
                <th className="label text-left px-5 py-3 hidden md:table-cell">Started</th>
                <th className="label text-left px-5 py-3">Work</th>
                <th className="label text-left px-5 py-3 hidden lg:table-cell">Break</th>
                <th className="label text-left px-5 py-3">Risk</th>
                <th className="label text-left px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array(8).fill(0).map((_, i) => (
                  <tr key={i} className="table-row">
                    <td colSpan={6} className="px-5 py-3">
                      <div className="h-4 bg-navy-700 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : filtered.map(s => (
                <tr key={s.id} className="table-row">
                  <td className="px-5 py-3">
                    <span className="font-mono text-xs text-sentinel-muted">{s.id?.slice(0, 8)}…</span>
                  </td>
                  <td className="px-5 py-3 hidden md:table-cell">
                    <span className="font-mono text-xs text-sentinel-text">{fmt(s.start_time)}</span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-1.5">
                      <Clock size={12} className="text-cyan-400" />
                      <span className="font-mono text-sm text-sentinel-text">{fmtMins(s.total_work_minutes)}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 hidden lg:table-cell">
                    <span className="font-mono text-sm text-sentinel-muted">{fmtMins(s.total_break_minutes)}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="font-mono text-sm text-amber-400">{Math.round(s.risk_score || 0)}</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className={statusBadge(s.status)}>{s.status}</span>
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
