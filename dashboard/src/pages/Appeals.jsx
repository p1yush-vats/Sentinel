import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { appealsAPI, employeesAPI } from '../services/api'
import { fromNow, initials, deptColor } from '../utils/helpers'
import { MessageSquare, CheckCircle, XCircle, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUS_BADGE = {
  pending:  'badge-medium',
  approved: 'badge-low',
  rejected: 'badge-critical',
}

export default function Appeals() {
  const navigate = useNavigate()
  const [appeals,       setAppeals]       = useState([])
  const [employees,     setEmployees]     = useState({})
  const [loading,       setLoading]       = useState(true)
  const [filter,        setFilter]        = useState('pending')
  const [expanded,      setExpanded]      = useState(null)
  const [adminResponse, setAdminResponse] = useState('')
  const [acting,        setActing]        = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([
      appealsAPI.getAll({ status: filter === 'all' ? undefined : filter, limit: 100 }),
      employeesAPI.getAll({ limit: 500 }),
    ])
      .then(([appRes, empRes]) => {
        setAppeals(appRes.data?.appeals || [])
        const map = {}
        ;(empRes.data?.employees || []).forEach(e => { map[e.id] = e })
        setEmployees(map)
      })
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

  return (
    <div className="space-y-5">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Appeals</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">Employee appeals against flagged sessions</p>
      </div>
      <div className="glow-line" />

      {/* Filter tabs */}
      <div className="flex gap-2 animate-fade-in stagger-1">
        {['all', 'pending', 'approved', 'rejected'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all capitalize
              ${filter === f ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20' : 'text-sentinel-muted border-sentinel-border hover:text-sentinel-text'}`}>
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-3 animate-fade-in stagger-2">
        {loading ? (
          Array(3).fill(0).map((_, i) => (
            <div key={i} className="card p-5">
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-navy-700 animate-pulse shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-navy-700 rounded animate-pulse w-1/3" />
                  <div className="h-3 bg-navy-700 rounded animate-pulse w-3/4" />
                </div>
              </div>
            </div>
          ))
        ) : appeals.length === 0 ? (
          <div className="card p-12 text-center">
            <MessageSquare size={28} className="text-sentinel-muted mx-auto mb-3" />
            <p className="font-display font-semibold text-sentinel-text">No {filter === 'all' ? '' : filter} appeals</p>
          </div>
        ) : (
          appeals.map((appeal, i) => {
            const emp   = employees[appeal.employee_id]
            const color = deptColor(emp?.department)

            return (
              <div key={appeal.id}
                className={`card p-5 transition-all duration-200 ${expanded === appeal.id ? 'border-cyan-400/15' : ''}`}>
                <div className="flex items-start gap-3">
                  {/* Avatar — clickable */}
                  {emp?.avatar_url ? (
                    <img
                      src={emp.avatar_url}
                      alt={emp.full_name}
                      onClick={() => navigate(`/employees/${emp.id}`)}
                      className="w-10 h-10 rounded-full object-cover shrink-0 cursor-pointer hover:opacity-80 transition-opacity border"
                      style={{ borderColor: color + '50' }}
                      onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
                    />
                  ) : null}
                  <div
                    onClick={() => emp && navigate(`/employees/${emp.id}`)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-mono font-bold shrink-0
                      ${emp ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}
                      ${emp?.avatar_url ? 'hidden' : ''}`}
                    style={{ backgroundColor: color + '18', color, border: `1.5px solid ${color}30` }}
                    title={emp?.full_name}
                  >
                    {emp ? initials(emp.full_name) : '??'}
                  </div>

                  <div className="flex-1 min-w-0 cursor-pointer" onClick={() => setExpanded(expanded === appeal.id ? null : appeal.id)}>
                    {/* Employee name */}
                    <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-medium text-sentinel-text">
                          {emp?.full_name || 'Unknown Employee'}
                        </p>
                        {emp?.department && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ backgroundColor: color + '18', color }}>
                            {emp.department}
                          </span>
                        )}
                      </div>
                      <span className={STATUS_BADGE[appeal.status]}>{appeal.status}</span>
                    </div>
                    <p className="text-sm text-sentinel-text line-clamp-2">{appeal.reason}</p>
                    <p className="text-xs font-mono text-sentinel-muted mt-1">{fromNow(appeal.created_at)}</p>
                  </div>

                  {emp && (
                    <button onClick={() => navigate(`/employees/${emp.id}`)}
                      className="w-7 h-7 rounded-lg hover:bg-navy-700 flex items-center justify-center text-sentinel-muted hover:text-cyan-400 transition-colors shrink-0">
                      <ExternalLink size={13} />
                    </button>
                  )}
                </div>

                {/* Expanded review panel */}
                {expanded === appeal.id && appeal.status === 'pending' && (
                  <div className="border-t border-sentinel-border mt-4 pt-4 space-y-3 animate-fade-in">
                    <p className="label">Full Reason</p>
                    <p className="text-sm text-sentinel-text bg-navy-900 rounded-lg p-3 font-mono leading-relaxed">
                      {appeal.reason}
                    </p>
                    <textarea
                      value={adminResponse}
                      onChange={e => setAdminResponse(e.target.value)}
                      placeholder="Admin response…"
                      rows={2}
                      className="input-field resize-none"
                    />
                    <div className="flex gap-2">
                      <button onClick={() => handleReview(appeal.id, 'approved')} disabled={acting === appeal.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-emerald-400/10 text-emerald-400 border border-emerald-400/20 hover:bg-emerald-400/20 transition-all disabled:opacity-50">
                        <CheckCircle size={12} /> {acting === appeal.id ? '…' : 'Approve'}
                      </button>
                      <button onClick={() => handleReview(appeal.id, 'rejected')} disabled={acting === appeal.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-red-400/10 text-red-400 border border-red-400/20 hover:bg-red-400/20 transition-all disabled:opacity-50">
                        <XCircle size={12} /> {acting === appeal.id ? '…' : 'Reject'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Show admin response if already reviewed */}
                {expanded === appeal.id && appeal.status !== 'pending' && appeal.admin_response && (
                  <div className="border-t border-sentinel-border mt-4 pt-4 animate-fade-in">
                    <p className="label mb-2">Admin Response</p>
                    <p className="text-sm font-mono text-sentinel-muted bg-navy-900 rounded-lg p-3">{appeal.admin_response}</p>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}