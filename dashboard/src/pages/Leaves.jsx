import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, CheckCircle, XCircle, Clock, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../services/api'
import { employeesAPI } from '../services/api'
import { initials, deptColor } from '../utils/helpers'

const STATUS_STYLE = {
  pending:  { badge: 'badge-medium',   icon: Clock,       color: 'text-amber-400'   },
  approved: { badge: 'badge-low',      icon: CheckCircle, color: 'text-emerald-400' },
  rejected: { badge: 'badge-critical', icon: XCircle,     color: 'text-red-400'     },
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

  const load = () => {
    setLoading(true)
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
      .catch(() => toast.error('Failed to load leave requests'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const filtered = filter === 'all' ? leaves : leaves.filter(l => l.status === filter)

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
      setLeaves(prev => prev.map(l =>
        l.id === id ? { ...l, status, admin_response: adminResponse } : l
      ))
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
        {['all', 'pending', 'approved', 'rejected'].map(f => (
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
                className={`card p-5 transition-all duration-300 ${leave.status === 'pending' ? 'hover:border-amber-400/20' : ''}`}>
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
                        <span className={`${TYPE_COLORS[leave.leave_type] || 'text-cyan-400'} text-xs font-mono font-bold`}>
                          {TYPE_NAMES[leave.leave_type] || leave.leave_type}
                        </span>
                        <span className={st.badge}>{leave.status}</span>
                      </div>
                    </div>

                    {/* Dates + days */}
                    <div className="flex items-center gap-4 mb-2 flex-wrap">
                      <span className="text-xs font-mono text-sentinel-text font-semibold">
                        {leave.from_date} → {leave.to_date}
                      </span>
                      <span className="text-xs font-mono text-sentinel-muted">
                        {leave.days_requested} working day{leave.days_requested !== 1 ? 's' : ''}
                      </span>
                    </div>

                    {/* Reason */}
                    <p className="text-xs text-sentinel-muted italic mb-2">
                      "{leave.reason}"
                    </p>

                    {/* Admin response if already reviewed */}
                    {leave.admin_response && leave.status !== 'pending' && (
                      <p className={`text-xs font-mono mt-1 ${leave.status === 'approved' ? 'text-emerald-400' : 'text-red-400'}`}>
                        ↳ {leave.admin_response}
                      </p>
                    )}

                    {/* Action panel — pending only */}
                    {leave.status === 'pending' && (
                      <div className="mt-3 space-y-2">
                        <input
                          type="text"
                          placeholder="Add a response (required before approving or rejecting)..."
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