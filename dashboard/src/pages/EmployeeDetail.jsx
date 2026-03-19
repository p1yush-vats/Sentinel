import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { employeesAPI, sessionsAPI, flagsAPI, appealsAPI } from '../services/api'
import {
  fmt, fmtDate, fmtMins, fromNow,
  deptColor, initials, statusBadge, severityBadge
} from '../utils/helpers'
import {
  AreaChart, Area, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts'
import {
  ArrowLeft, Clock, AlertTriangle, MessageSquare,
  Shield, Mail, Phone, Building2, BadgeCheck,
  UserX, UserCheck, ChevronDown, ChevronUp,
  Activity, Zap, Award
} from 'lucide-react'
import toast from 'react-hot-toast'
import SpotlightCard from '../components/ui/SpotlightCard'
import BorderGlow from '../components/ui/BorderGlow'

// ─── Tooltip ─────────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-navy-800 border border-sentinel-border rounded-lg px-3 py-2 text-xs font-mono shadow-xl">
      <p className="text-sentinel-muted mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: <span className="font-bold">{p.value}</span></p>
      ))}
    </div>
  )
}

// ─── Animated number ──────────────────────────────────────────
function AnimatedNumber({ value, duration = 900, suffix = '' }) {
  const [display, setDisplay] = useState(0)
  useEffect(() => {
    let raf
    const start = performance.now()
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1)
      const ease = 1 - Math.pow(1 - p, 3)
      setDisplay(Math.round(ease * value))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, duration])
  return <>{display.toLocaleString()}{suffix}</>
}

// ─── 3D Tilt card ─────────────────────────────────────────────
function TiltCard({ children, className = '' }) {
  const ref = useRef(null)
  const move = (e) => {
    const el = ref.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const x = (e.clientX - r.left) / r.width - 0.5
    const y = (e.clientY - r.top) / r.height - 0.5
    el.style.transform = `perspective(700px) rotateY(${x * 10}deg) rotateX(${-y * 10}deg) scale(1.03)`
  }
  const leave = () => {
    if (ref.current) ref.current.style.transform = 'perspective(700px) rotateY(0deg) rotateX(0deg) scale(1)'
  }
  return (
    <div ref={ref} onMouseMove={move} onMouseLeave={leave} className={className}
      style={{ transition: 'transform 0.18s ease', transformStyle: 'preserve-3d' }}>
      {children}
    </div>
  )
}

// ─── SVG ring progress ────────────────────────────────────────
function RingProgress({ value, max, size = 80, color = '#22d3ee', label, sublabel }) {
  const r = size / 2 - 8
  const circ = 2 * Math.PI * r
  const dash = Math.min(value / max, 1) * circ
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth="6" />
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="6"
            strokeDasharray={`${dash} ${circ - dash}`} strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 1.2s cubic-bezier(.4,0,.2,1)', filter: `drop-shadow(0 0 5px ${color}90)` }} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-display font-bold text-xs text-sentinel-text">
            {Math.round(Math.min(value / max, 1) * 100)}%
          </span>
        </div>
      </div>
      <p className="text-xs font-mono text-sentinel-text text-center leading-tight">{label}</p>
      {sublabel && <p className="text-[10px] font-mono text-sentinel-muted text-center">{sublabel}</p>}
    </div>
  )
}

// ─── Flag card ────────────────────────────────────────────────
function FlagCard({ flag }) {
  const [exp, setExp] = useState(false)
  const types = Object.keys(flag.detections || {})
  return (
    <SpotlightCard spotlightColor="rgba(239,68,68,0.07)"
      className="border border-sentinel-border rounded-xl overflow-hidden bg-navy-800">
      <div className="flex items-center gap-3 p-4 cursor-pointer select-none" onClick={() => setExp(e => !e)}>
        <div className="w-9 h-9 rounded-full bg-red-400/10 border border-red-400/20 flex items-center justify-center shrink-0">
          <AlertTriangle size={14} className="text-red-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={severityBadge(flag.overall_severity)}>{flag.overall_severity}</span>
            {types.slice(0, 2).map(t => (
              <span key={t} className="badge-medium text-[10px]">{t.replace(/_/g, ' ')}</span>
            ))}
            {types.length > 2 && <span className="text-[10px] font-mono text-sentinel-muted">+{types.length - 2}</span>}
          </div>
          <div className="flex gap-3 flex-wrap">
            <span className="text-[11px] font-mono text-sentinel-muted">
              {Math.round((flag.confidence_score || 0) * 100)}% confidence
            </span>
            <span className="text-[11px] font-mono text-sentinel-muted">{fromNow(flag.first_detected_at)}</span>
            <span className={`text-[11px] font-mono ${flag.reviewed ? 'text-emerald-400' : 'text-amber-400'}`}>
              {flag.reviewed ? `✓ ${flag.review_decision}` : '● pending review'}
            </span>
          </div>
        </div>
        {exp ? <ChevronUp size={14} className="text-sentinel-muted shrink-0" /> : <ChevronDown size={14} className="text-sentinel-muted shrink-0" />}
      </div>
      {exp && (
        <div className="border-t border-sentinel-border px-4 pb-4 pt-3 grid sm:grid-cols-2 gap-2 animate-fade-in">
          {types.map(t => {
            const d = flag.detections[t]
            return (
              <div key={t} className="flex items-center justify-between bg-navy-900 rounded-lg px-3 py-2 border border-sentinel-border/40">
                <div>
                  <p className="text-xs font-mono text-sentinel-text">{t.replace(/_/g, ' ')}</p>
                  <p className="text-[11px] font-mono text-sentinel-muted mt-0.5">
                    {d.occurrences}× · {Math.round((d.confidence || 0) * 100)}%
                  </p>
                </div>
                <span className={severityBadge(d.severity)}>{d.severity}</span>
              </div>
            )
          })}
        </div>
      )}
    </SpotlightCard>
  )
}

// ─── Main component ───────────────────────────────────────────
export default function EmployeeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [employee, setEmployee] = useState(null)
  const [sessions, setSessions] = useState([])
  const [flags,    setFlags]    = useState([])
  const [appeals,  setAppeals]  = useState([])
  const [loading,  setLoading]  = useState(true)
  const [tab,      setTab]      = useState('overview')
  const [toggling, setToggling] = useState(false)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      employeesAPI.getOne(id),
      sessionsAPI.getAll({ limit: 200, employee_id: id }),
      flagsAPI.getUnreviewed({ limit: 200 }),
      appealsAPI.getAll({ limit: 200 }),
    ])
      .then(([empRes, sessRes, flagsRes, appealsRes]) => {
        setEmployee(empRes.data)
        setSessions(sessRes.data?.sessions || [])
        setFlags((flagsRes.data?.abnormalities || []).filter(f => f.employee_id === id))
        setAppeals((appealsRes.data?.appeals || []).filter(a => a.employee_id === id))
      })
      .catch(() => toast.error('Failed to load employee'))
      .finally(() => setLoading(false))
  }, [id])

  const toggleActive = async () => {
    if (!employee || toggling) return
    setToggling(true)
    try {
      await employeesAPI.update(id, { is_active: !employee.is_active })
      setEmployee(e => ({ ...e, is_active: !e.is_active }))
      toast.success(`${employee.full_name} ${employee.is_active ? 'deactivated' : 'activated'}`)
    } catch { toast.error('Failed to update') }
    finally { setToggling(false) }
  }

  // ── Computed ──────────────────────────────────────────────
  const completed = sessions.filter(s => s.status === 'completed')
  const totalWork = sessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
  const avgWork   = completed.length ? Math.round(totalWork / completed.length) : 0
  const riskScore = Math.round(employee?.risk_score || 0)
  const color     = deptColor(employee?.department)

  const recentSessions = [...sessions]
    .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
    .slice(0, 10).reverse()
    .map((s, i) => ({
      label: `#${i + 1}`,
      work:  s.total_work_minutes || 0,
      risk:  Math.round(s.risk_score || 0),
      brk:   s.total_break_minutes || 0,
    }))

  const statusDist = ['completed','partial','flagged','abandoned','active']
    .map(st => ({
      name: st,
      value: sessions.filter(s => s.status === st).length,
      color: { completed:'#10b981', partial:'#f59e0b', flagged:'#ef4444', abandoned:'#64748b', active:'#22d3ee' }[st]
    })).filter(d => d.value > 0)

  const radarData = [
    { subject: 'Attendance',   value: Math.min(sessions.length * 8, 100) },
    { subject: 'Completion',   value: sessions.length ? Math.round(completed.length / sessions.length * 100) : 0 },
    { subject: 'Work Target',  value: Math.min(Math.round(avgWork / 400 * 100), 100) },
    { subject: 'Integrity',    value: Math.max(0, 100 - riskScore) },
    { subject: 'Consistency',  value: sessions.length > 3 ? 75 : 30 },
    { subject: 'Clean Record', value: Math.max(0, 100 - flags.length * 20) },
  ]

  const TABS = [
    { key: 'overview', label: 'Overview',  icon: Activity },
    { key: 'sessions', label: 'Sessions',  icon: Clock,         count: sessions.length },
    { key: 'flags',    label: 'Flags',     icon: AlertTriangle, count: flags.length },
    { key: 'appeals',  label: 'Appeals',   icon: MessageSquare, count: appeals.length },
  ]

  // ── Loading skeleton ──────────────────────────────────────
  if (loading) return (
    <div className="space-y-5 animate-fade-in">
      <div className="h-7 w-36 bg-navy-700 rounded animate-pulse" />
      <div className="h-52 bg-navy-700 rounded-2xl animate-pulse" />
      <div className="grid grid-cols-4 gap-4">
        {Array(4).fill(0).map((_, i) => <div key={i} className="h-24 bg-navy-700 rounded-xl animate-pulse" />)}
      </div>
    </div>
  )

  if (!employee) return (
    <div className="card p-12 text-center">
      <p className="text-sentinel-muted font-mono">Employee not found</p>
      <button onClick={() => navigate('/employees')} className="btn-ghost mt-4 mx-auto">← Back</button>
    </div>
  )

  return (
    <div className="space-y-5 animate-fade-in">

      {/* Back button */}
      <button onClick={() => navigate('/employees')}
        className="flex items-center gap-2 text-sm text-sentinel-muted hover:text-sentinel-text transition-colors font-mono group">
        <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform duration-200" />
        Back to Employees
      </button>

      {/* ══ HERO CARD ══ */}
      <BorderGlow glowColor={color} borderRadius="1rem">
        <div className="card rounded-2xl overflow-hidden relative p-6">
          {/* Decorative bg blob */}
          <div className="absolute top-0 right-0 w-72 h-72 rounded-full opacity-[0.04] blur-3xl pointer-events-none"
            style={{ background: color, transform: 'translate(25%,-25%)' }} />

          <div className="flex flex-col sm:flex-row gap-5 relative z-10">
            {/* Avatar */}
            <div className="relative shrink-0 self-start">
              {employee.avatar_url ? (
                <img src={employee.avatar_url} alt={employee.full_name}
                  className="w-24 h-24 rounded-2xl object-cover"
                  style={{ border: `2px solid ${color}50` }} />
              ) : (
                <div className="w-24 h-24 rounded-2xl flex items-center justify-center text-3xl font-display font-bold"
                  style={{ background: `linear-gradient(135deg, ${color}20, ${color}08)`, color, border: `2px solid ${color}30` }}>
                  {initials(employee.full_name)}
                </div>
              )}
              <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-navy-800 ${employee.is_active ? 'bg-emerald-400' : 'bg-slate-500'}`}
                style={employee.is_active ? { boxShadow: '0 0 8px #10b981' } : {}} />
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-start justify-between gap-3 mb-2">
                <div>
                  <h1 className="font-display font-bold text-3xl" style={{
                    background: `linear-gradient(90deg, #fff 0%, ${color} 50%, #fff 100%)`,
                    backgroundSize: '200% auto',
                    WebkitBackgroundClip: 'text', backgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    animation: 'shimmer 4s linear infinite'
                  }}>
                    {employee.full_name}
                  </h1>
                  <p className="font-mono text-sm mt-0.5" style={{ color }}>
                    {employee.position || employee.department || '—'}
                  </p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={employee.is_active ? 'badge-low' : 'badge-critical'}>
                    {employee.is_active ? '● Active' : '○ Inactive'}
                  </span>
                  <span className="badge-ok capitalize">{employee.role?.replace('_', ' ')}</span>
                  <button onClick={toggleActive} disabled={toggling}
                    className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg border transition-all disabled:opacity-50
                      ${employee.is_active ? 'border-red-500/20 text-red-400 hover:bg-red-400/10' : 'border-emerald-500/20 text-emerald-400 hover:bg-emerald-400/10'}`}>
                    {employee.is_active ? <UserX size={12} /> : <UserCheck size={12} />}
                    {toggling ? '...' : employee.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-1.5">
                {[
                  { icon: Mail, val: employee.email },
                  { icon: Phone, val: employee.phone },
                  { icon: Building2, val: employee.department },
                  { icon: BadgeCheck, val: employee.employee_code ? `#${employee.employee_code}` : null },
                  { icon: Shield, val: `Joined ${fmtDate(employee.created_at)}` },
                ].filter(i => i.val).map(({ icon: Icon, val }) => (
                  <span key={val} className="flex items-center gap-1.5 text-xs font-mono text-sentinel-muted">
                    <Icon size={11} className="shrink-0" /> {val}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Stat tiles */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-5 border-t border-sentinel-border relative z-10">
            {[
              { label: 'Total Sessions', value: sessions.length, color: '#22d3ee', icon: Activity, suffix: '' },
              { label: 'Completed',      value: completed.length, color: '#10b981', icon: Award, suffix: '' },
              { label: 'Avg Work/Day',   value: avgWork, color: '#f59e0b', icon: Clock, suffix: 'm' },
              { label: 'Risk Score',     value: riskScore, suffix: '/100',
                color: riskScore >= 75 ? '#ef4444' : riskScore >= 50 ? '#f97316' : riskScore >= 25 ? '#f59e0b' : '#10b981',
                icon: Zap },
            ].map(stat => (
              <TiltCard key={stat.label}>
                <SpotlightCard spotlightColor={stat.color + '18'}
                  className="bg-navy-900 border border-sentinel-border rounded-xl p-4 h-full">
                  <div className="flex items-start justify-between mb-2">
                    <p className="label text-[10px]">{stat.label}</p>
                    <div className="w-6 h-6 rounded-md flex items-center justify-center shrink-0"
                      style={{ background: stat.color + '20' }}>
                      <stat.icon size={12} style={{ color: stat.color }} />
                    </div>
                  </div>
                  <p className="font-display font-bold text-2xl" style={{ color: stat.color }}>
                    <AnimatedNumber value={stat.value} />{stat.suffix}
                  </p>
                </SpotlightCard>
              </TiltCard>
            ))}
          </div>
        </div>
      </BorderGlow>

      {/* ══ TABS ══ */}
      <div className="flex gap-1 p-1 bg-navy-800 border border-sentinel-border rounded-xl w-full sm:w-fit overflow-x-auto">
        {TABS.map(({ key, label, icon: Icon, count }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono transition-all duration-200 whitespace-nowrap
              ${tab === key ? 'bg-navy-700 text-sentinel-text' : 'text-sentinel-muted hover:text-sentinel-text'}`}>
            <Icon size={13} />
            {label}
            {count !== undefined && count > 0 && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full
                ${tab === key ? 'bg-cyan-400/20 text-cyan-400' : 'bg-navy-600 text-sentinel-muted'}`}>
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ══ OVERVIEW ══ */}
      {tab === 'overview' && (
        <div className="space-y-4 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Area chart */}
            <div className="lg:col-span-2 card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="section-title">Work Time Trend</h3>
                <span className="label">last {recentSessions.length} sessions</span>
              </div>
              {recentSessions.length === 0 ? (
                <p className="text-sentinel-muted font-mono text-sm text-center py-16">No session data yet</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={recentSessions}>
                    <defs>
                      <linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#22d3ee" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area type="monotone" dataKey="work" name="Work (min)" stroke="#22d3ee" strokeWidth={2} fill="url(#wg)" dot={{ fill: '#22d3ee', r: 3 }} activeDot={{ r: 5 }} />
                    <Area type="monotone" dataKey="risk" name="Risk Score"  stroke="#ef4444" strokeWidth={1.5} fill="url(#rg)" strokeDasharray="4 3" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Pie */}
            <div className="card p-5">
              <h3 className="section-title mb-4">Session Breakdown</h3>
              {statusDist.length === 0 ? (
                <p className="text-sentinel-muted font-mono text-sm text-center py-16">No data yet</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={statusDist} cx="50%" cy="45%" innerRadius={48} outerRadius={78} paddingAngle={3} dataKey="value">
                      {statusDist.map((e, i) => <Cell key={i} fill={e.color} opacity={0.85} />)}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                    <Legend iconType="circle" iconSize={7}
                      formatter={v => <span style={{ color: '#94a3b8', fontSize: 10, fontFamily: 'IBM Plex Mono' }}>{v}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Radar */}
            <div className="card p-5">
              <h3 className="section-title mb-4">Performance Radar</h3>
              <ResponsiveContainer width="100%" height={250}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#1e293b" />
                  <PolarAngleAxis dataKey="subject"
                    tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} />
                  <Radar dataKey="value" stroke={color} fill={color} fillOpacity={0.15} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Rings + bar */}
            <div className="card p-5 flex flex-col gap-5">
              <h3 className="section-title">Progress Rings</h3>
              <div className="flex justify-around flex-wrap gap-4">
                <RingProgress value={completed.length} max={Math.max(sessions.length, 1)}
                  color="#10b981" size={88} label="Completion" sublabel={`${completed.length}/${sessions.length}`} />
                <RingProgress value={Math.max(0, 100 - riskScore)} max={100}
                  color="#22d3ee" size={88} label="Integrity" sublabel={`Risk: ${riskScore}`} />
                <RingProgress value={Math.min(avgWork, 400)} max={400}
                  color="#f59e0b" size={88} label="Daily Target" sublabel={`${fmtMins(avgWork)} avg`} />
              </div>
              {recentSessions.length > 0 && (
                <div>
                  <p className="label mb-2">Work vs Break (last sessions)</p>
                  <ResponsiveContainer width="100%" height={90}>
                    <BarChart data={recentSessions} barSize={10} barGap={2}>
                      <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 9 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<ChartTooltip />} />
                      <Bar dataKey="work" name="Work (min)"  fill="#22d3ee" opacity={0.8} radius={[2,2,0,0]} />
                      <Bar dataKey="brk"  name="Break (min)" fill="#f59e0b" opacity={0.7} radius={[2,2,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ══ SESSIONS ══ */}
      {tab === 'sessions' && (
        <div className="card overflow-hidden animate-fade-in">
          <div className="flex items-center justify-between px-5 py-4 border-b border-sentinel-border">
            <h3 className="section-title">Session History</h3>
            <span className="label">{sessions.length} total · {fmtMins(totalWork)} worked</span>
          </div>
          {sessions.length === 0 ? (
            <p className="text-sentinel-muted font-mono text-sm text-center py-12">No sessions yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-sentinel-border/50">
                    <th className="label text-left px-5 py-3">Started</th>
                    <th className="label text-left px-5 py-3">Work</th>
                    <th className="label text-left px-5 py-3 hidden sm:table-cell">Break</th>
                    <th className="label text-left px-5 py-3 hidden md:table-cell">Lunch</th>
                    <th className="label text-left px-5 py-3 hidden md:table-cell">Risk</th>
                    <th className="label text-left px-5 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {[...sessions].sort((a,b) => new Date(b.start_time)-new Date(a.start_time)).map(s => (
                    <tr key={s.id} className="table-row">
                      <td className="px-5 py-3">
                        <p className="text-sm font-mono text-sentinel-text">{fmt(s.start_time)}</p>
                        {s.end_time && <p className="text-[11px] font-mono text-sentinel-muted">→ {fmt(s.end_time)}</p>}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-1.5">
                          <Clock size={12} className="text-cyan-400" />
                          <span className="font-mono text-sm">{fmtMins(s.total_work_minutes)}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 hidden sm:table-cell">
                        <span className="font-mono text-sm text-sentinel-muted">{fmtMins(s.total_break_minutes)}</span>
                      </td>
                      <td className="px-5 py-3 hidden md:table-cell">
                        <span className={`text-xs font-mono ${s.lunch_taken ? 'text-emerald-400' : 'text-sentinel-muted'}`}>
                          {s.lunch_taken ? '✓ taken' : '—'}
                        </span>
                      </td>
                      <td className="px-5 py-3 hidden md:table-cell">
                        <span className={`font-mono text-sm font-bold ${
                          (s.risk_score||0) >= 75 ? 'text-red-400' : (s.risk_score||0) >= 50 ? 'text-orange-400' :
                          (s.risk_score||0) >= 25 ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {Math.round(s.risk_score || 0)}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={statusBadge(s.status)}>{s.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ══ FLAGS ══ */}
      {tab === 'flags' && (
        <div className="space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <h3 className="section-title">Detected Flags</h3>
            {flags.filter(f => !f.reviewed).length > 0 && (
              <span className="badge-critical">{flags.filter(f => !f.reviewed).length} pending</span>
            )}
          </div>
          {flags.length === 0 ? (
            <div className="card p-14 text-center">
              <Shield size={36} className="text-emerald-400 mx-auto mb-3" />
              <p className="font-display font-semibold text-sentinel-text text-lg">Clean record</p>
              <p className="text-sentinel-muted text-sm font-mono mt-1">No abnormalities detected</p>
            </div>
          ) : flags.map(f => <FlagCard key={f.id} flag={f} />)}
        </div>
      )}

      {/* ══ APPEALS ══ */}
      {tab === 'appeals' && (
        <div className="space-y-3 animate-fade-in">
          <h3 className="section-title">Appeals</h3>
          {appeals.length === 0 ? (
            <div className="card p-12 text-center">
              <MessageSquare size={28} className="text-sentinel-muted mx-auto mb-3" />
              <p className="text-sentinel-muted font-mono text-sm">No appeals submitted</p>
            </div>
          ) : appeals.map(a => (
            <SpotlightCard key={a.id} spotlightColor="rgba(139,92,246,0.07)"
              className="border border-sentinel-border rounded-xl bg-navy-800 p-4">
              <div className="flex items-start justify-between gap-3 mb-2">
                <p className="text-sm text-sentinel-text leading-relaxed">{a.reason}</p>
                <span className={`shrink-0 ${
                  a.status === 'approved' ? 'badge-low' :
                  a.status === 'rejected' ? 'badge-critical' : 'badge-medium'}`}>
                  {a.status}
                </span>
              </div>
              <div className="flex flex-wrap gap-4">
                <span className="text-[11px] font-mono text-sentinel-muted">{fromNow(a.created_at)}</span>
                {a.admin_response && (
                  <span className="text-[11px] font-mono text-cyan-400">Admin: {a.admin_response}</span>
                )}
              </div>
            </SpotlightCard>
          ))}
        </div>
      )}
    </div>
  )
}