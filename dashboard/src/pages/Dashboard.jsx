import { useEffect, useState } from 'react'
import { Users, Clock, AlertTriangle, Activity, CheckCircle, TrendingUp } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import StatCard from '../components/dashboard/StatCard'
import LiveFeed from '../components/dashboard/LiveFeed'
import TopFlagged from '../components/dashboard/TopFlagged'
import RiskRadar from '../components/dashboard/RiskRadar'
import { employeesAPI, sessionsAPI, flagsAPI } from '../services/api'
import { fmtDate } from '../utils/helpers'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-navy-800 border border-sentinel-border rounded-lg px-3 py-2 text-xs font-mono">
      <p className="text-sentinel-muted mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value}</p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats]           = useState({ employees: 0, activeSessions: 0, flags: 0, resolved: 0 })
  const [sessionTrend, setSessionTrend] = useState([])
  const [topRisk, setTopRisk]       = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [empRes, sessRes, flagRes] = await Promise.all([
          employeesAPI.getAll({ limit: 100 }),
          sessionsAPI.getAll({ limit: 100 }),
          flagsAPI.getUnreviewed({ limit: 100 }),
        ])

        const employees = empRes.data?.employees || []
        const sessions  = sessRes.data?.sessions || []
        const flags     = flagRes.data?.abnormalities || []

        const activeSessions = sessions.filter(s => s.status === 'active').length

        // Build 7-day session trend
        const days = []
        for (let i = 6; i >= 0; i--) {
          const d = new Date()
          d.setDate(d.getDate() - i)
          const key = fmtDate(d.toISOString())
          const count = sessions.filter(s => fmtDate(s.start_time) === key).length
          const flagCount = flags.filter(f => fmtDate(f.first_detected_at) === key).length
          days.push({ date: key.slice(4), sessions: count, flags: flagCount })
        }

        // Top risky employees by risk_score
        const risky = employees
          .filter(e => e.risk_score > 0)
          .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))

        setStats({ employees: employees.length, activeSessions, flags: flags.length, resolved: sessions.filter(s => s.status === 'completed').length })
        setSessionTrend(days)
        setTopRisk(risky)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Dashboard</h1>
        <p className="text-sentinel-muted text-sm mt-1 font-mono">
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      <div className="glow-line" />

      {/* Stats */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Total Employees"  value={stats.employees}       icon={Users}          accent="cyan"   loading={loading} trendLabel="Active workforce" trend={0} />
        <StatCard label="Active Sessions"  value={stats.activeSessions}  icon={Activity}       accent="green"  loading={loading} trendLabel="Right now" trend={0} />
        <StatCard label="Pending Flags"    value={stats.flags}           icon={AlertTriangle}  accent="red"    loading={loading} trendLabel="Needs review" trend={stats.flags > 0 ? 1 : 0} />
        <StatCard label="Sessions Today"   value={stats.resolved}        icon={CheckCircle}    accent="purple" loading={loading} trendLabel="Completed" trend={0} />
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

        {/* Risk radar */}
        <RiskRadar />
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <TopFlagged employees={topRisk} loading={loading} />
        <div className="xl:col-span-2">
          <LiveFeed />
        </div>
      </div>
    </div>
  )
}
