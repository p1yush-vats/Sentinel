import { useEffect, useState } from 'react'
import { appealsAPI } from '../services/api'
import { fromNow, initials } from '../utils/helpers'
import { MessageSquare, CheckCircle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Appeals() {
  const [appeals,       setAppeals]       = useState([])
  const [loading,       setLoading]       = useState(true)
  const [filter,        setFilter]        = useState('pending')
  const [expanded,      setExpanded]      = useState(null)
  const [adminResponse, setAdminResponse] = useState('')
  const [acting,        setActing]        = useState(null)

  const load = () => {
    appealsAPI.getAll({ status: filter === 'all' ? undefined : filter, limit: 100 })
      .then(r => setAppeals(r.data?.appeals || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filter])

  const handleReview = async (id, status) => {
    if (!adminResponse.trim()) { toast.error('Add a response'); return }
    setActing(id)
    try {
      await appealsAPI.review(id, { status, admin_response: adminResponse })
      toast.success(`Appeal ${status}`)
      setAppeals(prev => prev.filter(a => a.id !== id))
      setExpanded(null)
      setAdminResponse('')
    } catch { toast.error('Failed to review appeal') }
    finally { setActing(null) }
  }

  const STATUS_BADGE = { pending: 'badge-medium', approved: 'badge-low', rejected: 'badge-critical' }

  return (
    <div className="space-y-5">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Appeals</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">Employee appeals against flagged sessions</p>
      </div>

      <div className="glow-line" />

      <div className="flex gap-2 animate-fade-in stagger-1">
        {['all', 'pending', 'approved', 'rejected'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all duration-200 capitalize
              ${filter === f ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20' : 'text-sentinel-muted border-sentinel-border hover:text-sentinel-text'}`}>
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-3 animate-fade-in stagger-2">
        {loading ? (
          Array(3).fill(0).map((_, i) => (
            <div key={i} className="card p-5">
              <div className="h-4 bg-navy-700 rounded animate-pulse w-1/2 mb-2" />
              <div className="h-3 bg-navy-700 rounded animate-pulse w-3/4" />
            </div>
          ))
        ) : appeals.length === 0 ? (
          <div className="card p-12 text-center">
            <MessageSquare size={28} className="text-sentinel-muted mx-auto mb-3" />
            <p className="font-display font-semibold text-sentinel-text">No {filter === 'all' ? '' : filter} appeals</p>
          </div>
        ) : (
          appeals.map((appeal, i) => (
            <div key={appeal.id} className={`card p-5 transition-all duration-200 ${expanded === appeal.id ? 'border-cyan-400/15' : ''}`}>
              <div className="flex items-start gap-3 cursor-pointer" onClick={() => setExpanded(expanded === appeal.id ? null : appeal.id)}>
                <div className="w-9 h-9 rounded-full bg-purple-400/10 border border-purple-400/20 flex items-center justify-center text-xs font-mono text-purple-400 font-bold shrink-0">
                  {initials('EMP')}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="text-sm font-mono text-sentinel-muted">Session: {appeal.session_id?.slice(0, 8)}…</span>
                    <span className={STATUS_BADGE[appeal.status]}>{appeal.status}</span>
                  </div>
                  <p className="text-sm text-sentinel-text mt-1.5 line-clamp-2">{appeal.reason}</p>
                  <p className="text-xs font-mono text-sentinel-muted mt-1">{fromNow(appeal.created_at)}</p>
                </div>
              </div>

              {expanded === appeal.id && appeal.status === 'pending' && (
                <div className="border-t border-sentinel-border mt-4 pt-4 space-y-3 animate-fade-in">
                  <p className="label">Full Reason</p>
                  <p className="text-sm text-sentinel-text bg-navy-900 rounded-lg p-3 font-mono">{appeal.reason}</p>
                  <textarea
                    value={adminResponse}
                    onChange={e => setAdminResponse(e.target.value)}
                    placeholder="Admin response..."
                    rows={2}
                    className="input-field resize-none"
                  />
                  <div className="flex gap-2">
                    <button onClick={() => handleReview(appeal.id, 'approved')} disabled={acting === appeal.id}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-emerald-400/10 text-emerald-400 border border-emerald-400/20 hover:bg-emerald-400/20 transition-all disabled:opacity-50">
                      <CheckCircle size={12} /> Approve
                    </button>
                    <button onClick={() => handleReview(appeal.id, 'rejected')} disabled={acting === appeal.id}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-red-400/10 text-red-400 border border-red-400/20 hover:bg-red-400/20 transition-all disabled:opacity-50">
                      <XCircle size={12} /> Reject
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
