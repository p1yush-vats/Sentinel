import { useState } from 'react'
import { Calendar, CheckCircle, XCircle, Clock } from 'lucide-react'
import toast from 'react-hot-toast'

// Leave system — stored locally until backend endpoint is added
// Backend endpoint: POST /leaves, GET /leaves/all, PATCH /leaves/{id}/review

const MOCK_LEAVES = [
  { id: '1', employee: 'Vikram Nair',   department: 'Engineering', type: 'Sick Leave',   from: '2026-03-20', to: '2026-03-21', reason: 'Medical appointment', status: 'pending',  submitted: '2026-03-18' },
  { id: '2', employee: 'Priya Sharma',  department: 'HR',          type: 'Casual Leave',  from: '2026-03-25', to: '2026-03-25', reason: 'Personal work',       status: 'pending',  submitted: '2026-03-17' },
  { id: '3', employee: 'Rahul Mehta',   department: 'Sales',       type: 'Earned Leave',  from: '2026-04-01', to: '2026-04-03', reason: 'Family function',      status: 'approved', submitted: '2026-03-10' },
  { id: '4', employee: 'Sneha Kapoor',  department: 'Finance',     type: 'Sick Leave',    from: '2026-03-19', to: '2026-03-19', reason: 'Fever',               status: 'approved', submitted: '2026-03-18' },
  { id: '5', employee: 'Aditya Kumar',  department: 'Engineering', type: 'Casual Leave',  from: '2026-03-22', to: '2026-03-22', reason: 'Personal',            status: 'rejected', submitted: '2026-03-15' },
]

const STATUS_STYLE = {
  pending:  { badge: 'badge-medium', icon: Clock,         color: 'text-amber-400' },
  approved: { badge: 'badge-low',    icon: CheckCircle,   color: 'text-emerald-400' },
  rejected: { badge: 'badge-critical', icon: XCircle,     color: 'text-red-400' },
}

const TYPE_COLORS = {
  'Sick Leave':   'text-red-400',
  'Casual Leave': 'text-cyan-400',
  'Earned Leave': 'text-purple-400',
}

export default function Leaves() {
  const [leaves,  setLeaves]  = useState(MOCK_LEAVES)
  const [filter,  setFilter]  = useState('all')
  const [acting,  setActing]  = useState(null)

  const filtered = filter === 'all' ? leaves : leaves.filter(l => l.status === filter)

  const stats = {
    pending:  leaves.filter(l => l.status === 'pending').length,
    approved: leaves.filter(l => l.status === 'approved').length,
    rejected: leaves.filter(l => l.status === 'rejected').length,
  }

  const act = (id, status) => {
    setActing(id)
    setTimeout(() => {
      setLeaves(prev => prev.map(l => l.id === id ? { ...l, status } : l))
      toast.success(`Leave request ${status}`)
      setActing(null)
    }, 600)
  }

  return (
    <div className="space-y-5">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Leave Requests</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">Manage employee leave applications</p>
      </div>

      <div className="glow-line" />

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 animate-fade-in stagger-1">
        {[
          { label: 'Pending',  value: stats.pending,  accent: 'bg-amber-400/10 border-amber-400/20 text-amber-400' },
          { label: 'Approved', value: stats.approved, accent: 'bg-emerald-400/10 border-emerald-400/20 text-emerald-400' },
          { label: 'Rejected', value: stats.rejected, accent: 'bg-red-400/10 border-red-400/20 text-red-400' },
        ].map(s => (
          <div key={s.label} className={`card p-4 border ${s.accent.split(' ')[1]} text-center`}>
            <p className="label mb-1">{s.label}</p>
            <p className={`font-display font-bold text-2xl ${s.accent.split(' ')[2]}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="flex gap-2 animate-fade-in stagger-2">
        {['all', 'pending', 'approved', 'rejected'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all duration-200 capitalize
              ${filter === f ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20' : 'text-sentinel-muted border-sentinel-border hover:text-sentinel-text'}`}>
            {f}
          </button>
        ))}
      </div>

      {/* Cards */}
      <div className="space-y-3 animate-fade-in stagger-3">
        {filtered.map((leave, i) => {
          const st = STATUS_STYLE[leave.status]
          const Icon = st.icon
          return (
            <div key={leave.id} className={`card p-5 transition-all duration-300 ${leave.status === 'pending' ? 'hover:border-amber-400/20' : ''}`}>
              <div className="flex items-start gap-4">
                <div className="w-9 h-9 rounded-full bg-navy-900 border border-sentinel-border flex items-center justify-center shrink-0">
                  <Calendar size={15} className="text-sentinel-muted" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div>
                      <p className="text-sm font-semibold text-sentinel-text">{leave.employee}</p>
                      <p className="text-xs font-mono text-sentinel-muted">{leave.department}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={TYPE_COLORS[leave.type] + ' text-xs font-mono'}>{leave.type}</span>
                      <span className={st.badge}>{leave.status}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 mt-2 flex-wrap">
                    <span className="text-xs font-mono text-sentinel-text">
                      {leave.from} → {leave.to}
                    </span>
                    <span className="text-xs font-mono text-sentinel-muted">
                      "{leave.reason}"
                    </span>
                  </div>

                  {leave.status === 'pending' && (
                    <div className="flex gap-2 mt-3">
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
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
