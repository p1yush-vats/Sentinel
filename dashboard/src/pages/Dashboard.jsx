import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Clock, AlertTriangle, Activity, CheckCircle, TrendingUp } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis } from 'recharts'
import StatCard from '../components/dashboard/StatCard'
import LiveFeed from '../components/dashboard/LiveFeed'
import TopFlagged from '../components/dashboard/TopFlagged'
import { employeesAPI, sessionsAPI, flagsAPI } from '../services/api'
import { format, subDays } from 'date-fns'

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+') || (iso.includes('-') && iso.lastIndexOf('-') > 7)) return iso
  return iso + 'Z'
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-navy-800 border border-sentinel-border rounded-lg px-3 py-2 text-xs font-mono">
      <p className="text-sentinel-muted mb-1">{label}</p>
      {payload.map((p, i) => <p key={i} style={{ color: p.color }}>{p.name}: {p.value}</p>)}
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [employees,     setEmployees]     = useState([])
  const [sessions,      setSessions]      = useState([])
  const [flags,         setFlags]         = useState([])
  const [sessionTrend,  setSessionTrend]  = useState([])
  const [topRisk,       setTopRisk]       = useState([])
  const [radarData,     setRadarData]     = useState([])
  const [loading,       setLoading]       = useState(true)

  useEffect(() => {
    Promise.all([
      employeesAPI.getAll({ limit: 200 }),
      sessionsAPI.getAll({ limit: 500 }),
      flagsAPI.getUnreviewed({ limit: 200 }),
    ]).then(([empRes, sessRes, flagRes]) => {
      const emps  = empRes.data?.employees    || []
      const sess  = sessRes.data?.sessions    || []
      const flgs  = flagRes.data?.abnormalities || []

      setEmployees(emps)
      setSessions(sess)
      setFlags(flgs)

      const parseDay = (raw) => {
        if (!raw) return ''
        const dt = new Date(raw.includes('Z') || raw.includes('+') ? raw : raw + 'Z')
        return format(dt, 'yyyy-MM-dd')
      }
      const todayStr = format(new Date(), 'yyyy-MM-dd')

      // ── 7-day session trend ─────────────────────────────
      const days = Array.from({ length: 7 }, (_, i) => {
        const d      = subDays(new Date(), 6 - i)
        const dayStr = format(d, 'yyyy-MM-dd')
        const label  = format(d, 'EEE')
        const count     = sess.filter(s => parseDay(s.start_time)          === dayStr).length
        const flagCount = flgs.filter(f => parseDay(f.first_detected_at)   === dayStr).length
        return { date: label, sessions: count, flags: flagCount }
      })
      setSessionTrend(days)

      // ── Top risky employees ─────────────────────────────
      const risky = emps
        .filter(e => (e.risk_score || 0) > 0)
        .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
      setTopRisk(risky)

      // ── Real risk radar from aggregated data ────────────
      const totalSess   = sess.length
      const completed   = sess.filter(s => s.status === 'completed').length
      const flaggedSess = sess.filter(s => s.status === 'flagged').length
      const avgRisk     = totalSess ? sess.reduce((a, s) => a + (s.risk_score || 0), 0) / totalSess : 0
      const lunchPct    = totalSess ? sess.filter(s => s.lunch_taken).length / totalSess * 100 : 0
      const pasteFlags  = flgs.filter(f => {
        const types = Object.keys(f.detections || {})
        return types.some(t => t.includes('paste'))
      }).length
      const idleFlags = flgs.filter(f => {
        const types = Object.keys(f.detections || {})
        return types.some(t => t.includes('idle'))
      }).length
      const mouseFlags = flgs.filter(f => {
        const types = Object.keys(f.detections || {})
        return types.some(t => t.includes('mouse'))
      }).length

      setRadarData([
        { subject: 'Idle Time',    value: Math.min(idleFlags  * 15, 100) },
        { subject: 'Paste Events', value: Math.min(pasteFlags * 12, 100) },
        { subject: 'Mouse Jigg.',  value: Math.min(mouseFlags * 20, 100) },
        { subject: 'Burst Typing', value: Math.min(flaggedSess * 10, 100) },
        { subject: 'Off-Target',   value: Math.max(0, 100 - (totalSess ? Math.round(completed / totalSess * 100) : 0)) },
        { subject: 'Risk Avg',     value: Math.round(avgRisk) },
      ])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  // ── Today's sessions (fixed) ─────────────────────────────
  const todayStr       = format(new Date(), 'yyyy-MM-dd')
  const parseDay = (raw) => {
    if (!raw) return ''
    const dt = new Date(raw.includes('Z') || raw.includes('+') ? raw : raw + 'Z')
    return format(dt, 'yyyy-MM-dd')
  }
  const todaySessions  = sessions.filter(s => parseDay(s.start_time) === todayStr)
  const activeSessions = sessions.filter(s => s.status === 'active')

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Dashboard</h1>
        <p className="text-sentinel-muted text-sm mt-1 font-mono">
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      <div className="glow-line" />

      {/* Stats — all numbers are real now */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Total Employees"  value={employees.length}        icon={Users}         accent="cyan"   loading={loading} trendLabel="Active workforce" trend={0} />
        <StatCard label="Active Sessions"  value={activeSessions.length}   icon={Activity}      accent="green"  loading={loading} trendLabel="Right now" trend={activeSessions.length > 0 ? 1 : 0} />
        <StatCard label="Pending Flags"    value={flags.length}            icon={AlertTriangle} accent="red"    loading={loading} trendLabel="Needs review" trend={flags.length > 0 ? 1 : 0} />
        <StatCard label="Sessions Today"   value={todaySessions.length}    icon={CheckCircle}   accent="purple" loading={loading} trendLabel="Started today" trend={0} />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Session trend */}
        <div className="xl:col-span-2 card p-5 animate-fade-in stagger-2">
          <div className="flex items-center justify-between mb-5">
            <h3 className="section-title">Session Activity</h3>
            <span className="label">Last 7 days</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={sessionTrend}>
              <defs>
                <linearGradient id="sessGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#22d3ee" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="flagGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="sessions" name="Sessions" stroke="#22d3ee" strokeWidth={1.5} fill="url(#sessGrad)" />
              <Area type="monotone" dataKey="flags"    name="Flags"    stroke="#ef4444" strokeWidth={1.5} fill="url(#flagGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Real risk radar */}
        <div className="card p-5 animate-fade-in stagger-3">
          <h3 className="section-title mb-1">Risk Distribution</h3>
          <p className="text-[11px] font-mono text-sentinel-muted mb-3">Flagged behaviour patterns</p>
          {loading ? <div className="h-48 bg-navy-700 rounded animate-pulse" /> : (
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#162848" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 9, fontFamily: 'IBM Plex Mono' }} />
                <Radar dataKey="value" stroke="#ef4444" fill="#ef4444" fillOpacity={0.12} strokeWidth={1.5} />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <TopFlagged employees={topRisk} loading={loading} onEmployeeClick={id => navigate(`/employees/${id}`)} />
        <div className="xl:col-span-2">
          <LiveFeed />
        </div>
      </div>
    </div>
  )
}