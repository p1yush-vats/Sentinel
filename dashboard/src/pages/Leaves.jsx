import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, CheckCircle, XCircle, Clock, ExternalLink, MessageCircle, ScrollText } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../services/api'
import { employeesAPI } from '../services/api'
import { initials, deptColor, fromNow } from '../utils/helpers'

const STATUS_STYLE = {
  pending:  { badge: 'badge-medium',   icon: Clock,       color: 'text-amber-400'   },
  approved: { badge: 'badge-low',      icon: CheckCircle, color: 'text-emerald-400' },
  rejected: { badge: 'badge-critical', icon: XCircle,     color: 'text-red-400'     },
  needs_info: { badge: 'badge-medium', icon: MessageCircle, color: 'text-blue-400' },
}

const TYPE_COLORS = {
  EL: 'text-blue-400',
  CL: 'text-red-400',
  SL: 'text-amber-400',
  ML: 'text-pink-400',
}

const TYPE_NAMES = {
  EL: 'Earned Leave',
  CL: 'Casual Leave',
  SL: 'Sick Leave',
  ML: 'Maternity Leave',
}

function Avatar({ emp, size = 9 }) {
  const color = deptColor(emp?.department)
  if (emp?.avatar_url) {
    return (
      <img
        src={emp.avatar_url}
        alt={emp.full_name}
        className={`w-${size} h-${size} rounded-full object-cover shrink-0 border`}
        style={{ borderColor: color + '50' }}
        onError={e => { e.target.style.display = 'none' }}
      />
    )
  }
  return (
    <div
      className={`w-${size} h-${size} rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0`}
      style={{ backgroundColor: color + '18', color, border: `1.5px solid ${color}40` }}
    >
      {emp ? initials(emp.full_name) : '??'}
    </div>
  )
}

export default function Leaves() {
  const navigate  = useNavigate()
  const [leaves,    setLeaves]    = useState([])
  const [empMap,    setEmpMap]    = useState({})   // id → employee
  const [loading,   setLoading]   = useState(true)
  const [filter,    setFilter]    = useState('all')
  const [acting,    setActing]    = useState(null)
  const [response,  setResponse]  = useState({})
  const [showCert,  setShowCert]  = useState({})   // id → bool

  const load = (silent = false) => {
    if (!silent) setLoading(true)
    Promise.all([
      api.get('/leaves/all'),
      employeesAPI.getAll({ limit: 500 }),
    ])
      .then(([lRes, eRes]) => {
        setLeaves(lRes.data?.leaves || [])
        const map = {}
        ;(eRes.data?.employees || []).forEach(e => { map[e.id] = e })
        setEmpMap(map)
      })
      .catch(() => {
        if (!silent) toast.error('Failed to load leave requests')
      })
      .finally(() => {
        if (!silent) setLoading(false)
      })
  }

  useEffect(() => { 
    load()
    const interval = setInterval(() => load(true), 15000)
    return () => clearInterval(interval)
  }, [])

  const filtered = useMemo(() => {
    let result = filter === 'all' ? leaves : leaves.filter(l => l.status === filter)
    // Sort pending first, then everything else (assuming mostly date-ordered from API)
    return result.sort((a, b) => {
      if ((a.status === 'pending' || a.status === 'needs_info') && (b.status !== 'pending' && b.status !== 'needs_info')) return -1
      if ((b.status === 'pending' || b.status === 'needs_info') && (a.status !== 'pending' && a.status !== 'needs_info')) return 1
      return 0
    })
  }, [leaves, filter])

  const stats = {
    pending:  leaves.filter(l => l.status === 'pending').length,
    approved: leaves.filter(l => l.status === 'approved').length,
    rejected: leaves.filter(l => l.status === 'rejected').length,
  }

  const act = async (id, status) => {
    const adminResponse = response[id]?.trim()
    if (!adminResponse) {
      toast.error('Please add a response before deciding')
      return
    }
    setActing(id)
    try {
      await api.post(`/leaves/${id}/review`, { status, admin_response: adminResponse })
      toast.success(`Leave request ${status}`)
      setLeaves(prev => prev.map(l => {
        if (l.id === id) {
          const newComments = status === 'needs_info' && adminResponse
            ? [...(l.comments || []), { sender: 'admin', message: adminResponse, timestamp: new Date().toISOString() }]
            : (l.comments || [])
          return { ...l, status, admin_response: status === 'needs_info' ? l.admin_response : adminResponse, comments: newComments }
        }
        return l
      }))
      setResponse(prev => ({ ...prev, [id]: '' }))
    } catch (e) {
      toast.error(e.response?.data?.detail || `Failed to ${status} leave`)
    } finally {
      setActing(null)
    }
  }

  return (
    <div className="space-y-5">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Leave Requests</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">
          Manage employee leave applications — {leaves.length} total
        </p>
      </div>

      <div className="glow-line" />

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 animate-fade-in stagger-1">
        {[
          { label: 'Pending',  value: stats.pending,  accent: 'bg-amber-400/10 border-amber-400/20 text-amber-400'   },
          { label: 'Approved', value: stats.approved, accent: 'bg-emerald-400/10 border-emerald-400/20 text-emerald-400' },
          { label: 'Rejected', value: stats.rejected, accent: 'bg-red-400/10 border-red-400/20 text-red-400'         },
        ].map(s => (
          <div key={s.label} className={`card p-4 border ${s.accent.split(' ')[1]} text-center`}>
            <p className="label mb-1">{s.label}</p>
            <p className={`font-display font-bold text-2xl ${s.accent.split(' ')[2]}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 animate-fade-in stagger-2 flex-wrap">
        {['all', 'pending', 'needs_info', 'approved', 'rejected'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all duration-200 capitalize
              ${filter === f
                ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20'
                : 'text-sentinel-muted border-sentinel-border hover:text-sentinel-text'}`}>
            {f}
          </button>
        ))}
      </div>

      {/* Cards */}
      {loading ? (
        Array(3).fill(0).map((_, i) => (
          <div key={i} className="card p-5 animate-fade-in">
            <div className="flex gap-3">
              <div className="w-10 h-10 rounded-full bg-navy-700 animate-pulse shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-navy-700 rounded animate-pulse w-1/3" />
                <div className="h-3 bg-navy-700 rounded animate-pulse w-1/2" />
              </div>
            </div>
          </div>
        ))
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center animate-fade-in">
          <Calendar size={28} className="text-sentinel-muted mx-auto mb-3" />
          <p className="text-sentinel-muted text-sm font-mono">
            {filter === 'all' ? 'No leave requests yet' : `No ${filter} requests`}
          </p>
        </div>
      ) : (
        <div className="space-y-3 animate-fade-in stagger-3">
          {filtered.map(leave => {
            const emp   = empMap[leave.employee_id]
            const color = deptColor(emp?.department)
            const st    = STATUS_STYLE[leave.status] || STATUS_STYLE.pending

            return (
              <div key={leave.id}
                className={`card p-5 transition-all duration-300 ${(leave.status === 'pending' || leave.status === 'needs_info') ? 'hover:border-amber-400/20' : ''}`}>
                <div className="flex items-start gap-4">

                  {/* Avatar — clickable → employee detail */}
                  <div
                    onClick={() => emp && navigate(`/employees/${emp.id}`)}
                    className={emp ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}
                  >
                    <Avatar emp={emp} size={10} />
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Header row */}
                    <div className="flex items-start justify-between gap-3 flex-wrap mb-2">
                      <div className="min-w-0">
                        {/* Employee name — resolved from map */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <p
                            onClick={() => emp && navigate(`/employees/${emp.id}`)}
                            className={`text-sm font-semibold text-sentinel-text ${emp ? 'cursor-pointer hover:text-cyan-300 transition-colors' : ''}`}
                          >
                            {emp?.full_name || leave.employee_name || `${leave.employee_id?.slice(0, 8)}…`}
                          </p>
                          {emp && (
                            <button
                              onClick={() => navigate(`/employees/${emp.id}`)}
                              className="w-5 h-5 rounded flex items-center justify-center text-sentinel-muted hover:text-cyan-400 transition-colors"
                            >
                              <ExternalLink size={11} />
                            </button>
                          )}
                        </div>

                        {/* Department + position */}
                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                          {emp?.department && (
                            <span
                              className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded"
                              style={{ backgroundColor: color + '18', color }}
                            >
                              {emp.department}
                            </span>
                          )}
                          {emp?.position && (
                            <span className="text-[10px] font-mono text-sentinel-muted">{emp.position}</span>
                          )}
                          {!emp && (
                            <span className="text-[10px] font-mono text-sentinel-muted">Employee</span>
                          )}
                        </div>
                      </div>

                      {/* Leave type + status */}
                      <div className="flex items-center gap-2 flex-wrap shrink-0">
                        <span className={`${TYPE_COLORS[leave.leave_type] || 'text-cyan-400'} text-[11px] uppercase tracking-wider font-mono font-bold`}>
                          {TYPE_NAMES[leave.leave_type] || leave.leave_type}
                        </span>
                        <span className={st.badge}>{leave.status}</span>
                      </div>
                    </div>

                    {/* Dates + days */}
                    <div className="flex items-center gap-4 flex-wrap mt-2">
                      <span className="text-sm font-mono text-sentinel-text font-semibold flex items-center gap-1.5">
                        <Calendar size={13} className="text-sentinel-muted" />
                        {leave.from_date} → {leave.to_date}
                      </span>
                      <span className="text-xs font-mono text-sentinel-muted bg-navy-800 px-2 py-0.5 rounded border border-sentinel-border">
                        {leave.days_requested} working day{leave.days_requested !== 1 ? 's' : ''}
                      </span>
                      {leave.created_at && (
                        <span className="text-[10px] font-mono text-sentinel-muted ml-auto">
                          Applied {fromNow(leave.created_at)}
                        </span>
                      )}
                    </div>
                    
                    {/* Reason */}
                    <div className="mt-3 bg-navy-900/50 rounded-lg p-3 border border-sentinel-border/50">
                      <p className="text-xs text-sentinel-muted italic">
                        "{leave.reason}"
                      </p>
                    </div>

                    {/* Medical Evidence */}
                    {leave.medical_certificate && (
                      <div className="mt-3">
                        <button
                          onClick={() => setShowCert(prev => ({ ...prev, [leave.id]: !prev[leave.id] }))}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-pink-400/10 text-pink-400 border border-pink-400/20 hover:bg-pink-400/20 transition-all mb-2"
                        >
                          <ScrollText size={12} />
                          {showCert[leave.id] ? 'Hide Evidence' : 'View Medical Evidence'}
                        </button>
                        {showCert[leave.id] && (
                          <div className="rounded-lg border border-pink-400/30 overflow-hidden bg-navy-900/80 p-2 animate-fade-in">
                            {leave.medical_certificate.startsWith('data:image/') || leave.medical_certificate.startsWith('http') ? (
                              <img 
                                src={leave.medical_certificate} 
                                alt="Medical Evidence" 
                                className="w-full max-h-[400px] object-contain rounded"
                              />
                            ) : (
                              <div className="p-4 text-center">
                                <p className="text-xs font-mono text-sentinel-muted mb-2">PDF Document</p>
                                <a 
                                  href={leave.medical_certificate} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-cyan-400 text-xs font-bold hover:underline inline-flex items-center gap-1"
                                >
                                  Open Certificate in New Tab <ExternalLink size={10} />
                                </a>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Thread rendering */}
                    {leave.comments && leave.comments.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {leave.comments.map((c, idx) => (
                          <div key={idx} className={`p-2 rounded border text-xs font-mono max-w-[85%] ${c.sender === 'admin' ? 'bg-cyan-900/20 border-cyan-400/20 text-cyan-300 ml-auto text-right' : 'bg-navy-800 border-sentinel-border/50 text-sentinel-text mr-auto'}`}>
                            <div className="opacity-50 text-[9px] mb-1">{c.sender === 'admin' ? 'You' : emp?.full_name || 'Employee'} • {new Date(c.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                            {c.message}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Admin response if already reviewed */}
                    {leave.admin_response && leave.status !== 'pending' && (
                      <p className={`text-xs font-mono mt-1 ${leave.status === 'approved' ? 'text-emerald-400' : 'text-red-400'}`}>
                        ↳ {leave.admin_response}
                      </p>
                    )}

                    {/* Action panel — pending or needs_info only */}
                    {(leave.status === 'pending' || leave.status === 'needs_info') && (
                      <div className="mt-3 space-y-2">
                        <input
                          type="text"
                          placeholder={leave.status === 'needs_info' ? "Wait for employee reply, or send another message..." : "Add a response (required before deciding)..."}
                          value={response[leave.id] || ''}
                          onChange={e => setResponse(prev => ({ ...prev, [leave.id]: e.target.value }))}
                          className="input-field text-xs py-2"
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => act(leave.id, 'approved')}
                            disabled={acting === leave.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-emerald-400/10 text-emerald-400 border border-emerald-400/20 hover:bg-emerald-400/20 transition-all disabled:opacity-50"
                          >
                            <CheckCircle size={12} />
                            {acting === leave.id ? '...' : 'Approve'}
                          </button>
                          <button
                            onClick={() => act(leave.id, 'rejected')}
                            disabled={acting === leave.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-red-400/10 text-red-400 border border-red-400/20 hover:bg-red-400/20 transition-all disabled:opacity-50"
                          >
                            <XCircle size={12} />
                            {acting === leave.id ? '...' : 'Reject'}
                          </button>
                          <button
                            onClick={() => act(leave.id, 'needs_info')}
                            disabled={acting === leave.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-cyan-400/10 text-cyan-400 border border-cyan-400/20 hover:bg-cyan-400/20 transition-all disabled:opacity-50 ml-auto"
                          >
                            <MessageCircle size={12} />
                            {acting === leave.id ? '...' : 'Elaborate'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}