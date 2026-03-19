import { useEffect, useState, useMemo } from 'react'
import { employeesAPI, sessionsAPI, flagsAPI } from '../services/api'
import { fmtMins, deptColor, initials, fromNow } from '../utils/helpers'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
  AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis
} from 'recharts'
import { subDays, format } from 'date-fns'

const CustomTooltip = ({ active, payload, label }) => {
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

const DEPT_COLORS = ['#22d3ee', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#f97316']
const PERIODS = [
  { key: 'week',  label: 'This Week',  days: 7  },
  { key: 'month', label: 'This Month', days: 30 },
  { key: 'all',   label: 'All Time',   days: null },
]

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+') || (iso.includes('-') && iso.lastIndexOf('-') > 7)) return iso
  return iso + 'Z'
}

export default function Analytics() {
  const [employees,  setEmployees]  = useState([])
  const [sessions,   setSessions]   = useState([])
  const [flags,      setFlags]      = useState([])
  const [loading,    setLoading]    = useState(true)
  const [period,     setPeriod]     = useState('week')

  useEffect(() => {
    Promise.all([
      employeesAPI.getAll({ limit: 500 }),
      sessionsAPI.getAll({ limit: 1000 }),
      flagsAPI.getUnreviewed({ limit: 500 }),
    ]).then(([empRes, sessRes, flagRes]) => {
      setEmployees(empRes.data?.employees || [])
      setSessions(sessRes.data?.sessions  || [])
      setFlags(flagRes.data?.abnormalities || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  // ── Filter sessions by period ──────────────────────────────
  const filteredSessions = useMemo(() => {
    const p = PERIODS.find(p => p.key === period)
    if (!p.days) return sessions
    // Use plain Date comparison — strip timezone and compare date strings
    // to avoid IST↔UTC mismatch with date-fns isAfter
    const cutoff = subDays(new Date(), p.days)
    cutoff.setHours(0, 0, 0, 0)
    return sessions.filter(s => {
      try {
        // Parse as UTC by appending Z if missing, then compare timestamps
        const raw = s.start_time
        const dt  = new Date(raw.includes('Z') || raw.includes('+') ? raw : raw + 'Z')
        return dt >= cutoff
      } catch { return false }
    })
  }, [sessions, period])

  const filteredFlags = useMemo(() => {
    const p = PERIODS.find(p => p.key === period)
    if (!p.days) return flags
    const cutoff = subDays(new Date(), p.days)
    cutoff.setHours(0, 0, 0, 0)
    return flags.filter(f => {
      try {
        const raw = f.first_detected_at
        const dt  = new Date(raw.includes('Z') || raw.includes('+') ? raw : raw + 'Z')
        return dt >= cutoff
      } catch { return false }
    })
  }, [flags, period])

  // ── Department stats ───────────────────────────────────────
  const deptStats = useMemo(() => {
    const map = {}
    employees.forEach(e => {
      if (!e.department) return
      if (!map[e.department]) map[e.department] = { name: e.department, employees: 0, totalWork: 0, sessions: 0 }
      map[e.department].employees++
    })
    filteredSessions.forEach(s => {
      const emp = employees.find(e => e.id === s.employee_id)
      if (!emp?.department || !map[emp.department]) return
      map[emp.department].totalWork += s.total_work_minutes || 0
      map[emp.department].sessions++
    })
    return Object.values(map).map(d => ({
      ...d,
      avgWork: d.sessions > 0 ? Math.round(d.totalWork / d.sessions) : 0
    })).sort((a, b) => b.avgWork - a.avgWork)
  }, [employees, filteredSessions])

  // ── Top performers ─────────────────────────────────────────
  const topWorkers = useMemo(() => {
    const map = {}
    employees.forEach(e => { map[e.id] = { ...e, totalWork: 0, sessionCount: 0 } })
    filteredSessions.forEach(s => {
      if (map[s.employee_id]) {
        map[s.employee_id].totalWork    += s.total_work_minutes || 0
        map[s.employee_id].sessionCount += 1
      }
    })
    return Object.values(map).filter(e => e.totalWork > 0)
      .sort((a, b) => b.totalWork - a.totalWork).slice(0, 8)
  }, [employees, filteredSessions])

  // ── Daily sessions trend ──────────────────────────────────
  const dailyTrend = useMemo(() => {
    const days = period === 'week' ? 7 : period === 'month' ? 30 : 14
    return Array.from({ length: days }, (_, i) => {
      const d      = subDays(new Date(), days - 1 - i)
      const label  = format(d, days <= 7 ? 'EEE' : 'MMM d')
      const dayStr = format(d, 'yyyy-MM-dd')

      const parseDay = (raw) => {
        if (!raw) return ''
        const dt = new Date(raw.includes('Z') || raw.includes('+') ? raw : raw + 'Z')
        return format(dt, 'yyyy-MM-dd')
      }

      const count     = filteredSessions.filter(s => parseDay(s.start_time)          === dayStr).length
      const flagCount = filteredFlags.filter(f    => parseDay(f.first_detected_at)   === dayStr).length
      return { label, sessions: count, flags: flagCount }
    })
  }, [filteredSessions, filteredFlags, period])

  // ── Status distribution pie ────────────────────────────────
  const statusDist = useMemo(() => [
    { name: 'Completed', value: filteredSessions.filter(s => s.status === 'completed').length, color: '#10b981' },
    { name: 'Active',    value: filteredSessions.filter(s => s.status === 'active').length,    color: '#22d3ee' },
    { name: 'Partial',   value: filteredSessions.filter(s => s.status === 'partial').length,   color: '#f59e0b' },
    { name: 'Flagged',   value: filteredSessions.filter(s => s.status === 'flagged').length,   color: '#ef4444' },
    { name: 'Abandoned', value: filteredSessions.filter(s => s.status === 'abandoned').length, color: '#64748b' },
  ].filter(d => d.value > 0), [filteredSessions])

  // ── Radar — org-level metrics ──────────────────────────────
  const radarData = useMemo(() => {
    const total    = filteredSessions.length
    const done     = filteredSessions.filter(s => s.status === 'completed').length
    const avgRisk  = total ? filteredSessions.reduce((a, s) => a + (s.risk_score || 0), 0) / total : 0
    const flagRate = total ? (filteredFlags.length / total) * 100 : 0
    const lunchPct = total ? (filteredSessions.filter(s => s.lunch_taken).length / total) * 100 : 0
    return [
      { subject: 'Completion',  value: total ? Math.round(done / total * 100) : 0 },
      { subject: 'Punctuality', value: Math.max(0, Math.round(100 - flagRate)) },
      { subject: 'Avg Work',    value: Math.min(100, Math.round((filteredSessions.reduce((a,s) => a+(s.total_work_minutes||0),0) / Math.max(total,1)) / 400 * 100)) },
      { subject: 'Integrity',   value: Math.max(0, Math.round(100 - avgRisk)) },
      { subject: 'Lunch Break', value: Math.round(lunchPct) },
      { subject: 'Consistency', value: Math.min(100, total * 5) },
    ]
  }, [filteredSessions, filteredFlags])

  // ── Summary stats ──────────────────────────────────────────
  const totalWorkMins   = filteredSessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
  const completionRate  = filteredSessions.length
    ? Math.round(filteredSessions.filter(s => s.status === 'completed').length / filteredSessions.length * 100) : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 animate-fade-in">
        <div>
          <h1 className="font-display font-bold text-2xl text-sentinel-text">Analytics</h1>
          <p className="text-sentinel-muted text-sm font-mono mt-1">
            {filteredSessions.length} sessions · {fmtMins(totalWorkMins)} worked · {completionRate}% completion
          </p>
        </div>
        {/* Period filter — actually wired up now */}
        <div className="flex gap-1 p-1 bg-navy-800 border border-sentinel-border rounded-xl">
          {PERIODS.map(p => (
            <button key={p.key} onClick={() => setPeriod(p.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all duration-200
                ${period === p.key ? 'bg-navy-700 text-cyan-400 border border-cyan-400/20' : 'text-sentinel-muted hover:text-sentinel-text'}`}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="glow-line" />

      {/* Summary stat tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 animate-fade-in stagger-1">
        {[
          { label: 'Sessions',    value: filteredSessions.length,  color: 'text-cyan-400' },
          { label: 'Flags',       value: filteredFlags.length,     color: 'text-red-400' },
          { label: 'Completion',  value: `${completionRate}%`,     color: 'text-emerald-400' },
          { label: 'Total Work',  value: fmtMins(totalWorkMins),   color: 'text-amber-400' },
        ].map(s => (
          <div key={s.label} className="card p-4">
            <p className="label mb-1">{s.label}</p>
            <p className={`font-display font-bold text-2xl ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Daily trend + radar */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 animate-fade-in stagger-2">
        <div className="xl:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="section-title">Daily Activity</h3>
            <span className="label">{PERIODS.find(p => p.key === period)?.label}</span>
          </div>
          {loading ? <div className="h-48 bg-navy-700 rounded animate-pulse" /> : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={dailyTrend}>
                <defs>
                  <linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#22d3ee" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="sessions" name="Sessions" stroke="#22d3ee" strokeWidth={2} fill="url(#sg)" dot={{ fill: '#22d3ee', r: 3 }} />
                <Area type="monotone" dataKey="flags"    name="Flags"    stroke="#ef4444" strokeWidth={1.5} fill="url(#fg)" dot={false} strokeDasharray="4 2" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Org radar */}
        <div className="card p-5">
          <h3 className="section-title mb-1">Org Health</h3>
          <p className="text-[11px] font-mono text-sentinel-muted mb-3">Aggregate performance</p>
          {loading ? <div className="h-48 bg-navy-700 rounded animate-pulse" /> : (
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#162848" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 9, fontFamily: 'IBM Plex Mono' }} />
                <Radar dataKey="value" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.12} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Dept avg work + session distribution */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 animate-fade-in stagger-3">
        <div className="xl:col-span-2 card p-5">
          <h3 className="section-title mb-1">Avg Work Minutes by Department</h3>
          <p className="text-[11px] font-mono text-sentinel-muted mb-4">Minutes per session average</p>
          {loading ? <div className="h-48 bg-navy-700 rounded animate-pulse" /> : deptStats.length === 0 ? (
            <p className="text-sentinel-muted text-sm font-mono text-center py-12">No data for this period</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={deptStats} barSize={28}>
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} unit=" min" />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="avgWork" name="Avg Work (min)" radius={[4, 4, 0, 0]}>
                  {deptStats.map((_, i) => <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} opacity={0.85} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card p-5">
          <h3 className="section-title mb-1">Session Status</h3>
          <p className="text-[11px] font-mono text-sentinel-muted mb-3">Distribution breakdown</p>
          {loading ? <div className="h-48 bg-navy-700 rounded animate-pulse" /> : statusDist.length === 0 ? (
            <p className="text-sentinel-muted text-sm font-mono text-center py-12">No sessions this period</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={statusDist} cx="50%" cy="45%" innerRadius={52} outerRadius={82} paddingAngle={3} dataKey="value">
                  {statusDist.map((e, i) => <Cell key={i} fill={e.color} opacity={0.85} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend iconType="circle" iconSize={8}
                  formatter={v => <span style={{ color: '#94a3b8', fontSize: 11, fontFamily: 'IBM Plex Mono' }}>{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Top performers */}
      <div className="card p-5 animate-fade-in stagger-4">
        <div className="flex items-center justify-between mb-5">
          <h3 className="section-title">Top Performers</h3>
          <span className="label">{PERIODS.find(p => p.key === period)?.label}</span>
        </div>
        {loading ? (
          Array(5).fill(0).map((_, i) => (
            <div key={i} className="flex items-center gap-4 py-3 border-b border-sentinel-border/30">
              <div className="w-6 h-6 bg-navy-700 rounded animate-pulse" />
              <div className="flex-1 h-4 bg-navy-700 rounded animate-pulse" />
            </div>
          ))
        ) : topWorkers.length === 0 ? (
          <p className="text-sentinel-muted text-sm font-mono text-center py-8">No data for this period</p>
        ) : topWorkers.map((emp, i) => {
          const maxWork = topWorkers[0]?.totalWork || 1
          const pct = (emp.totalWork / maxWork) * 100
          const c = deptColor(emp.department)
          return (
            <div key={emp.id} className={`flex items-center gap-4 py-3 border-b border-sentinel-border/30 last:border-0 animate-fade-in stagger-${Math.min(i+1,5)}`}>
              <span className={`font-mono font-bold text-sm w-6 text-center shrink-0
                ${i === 0 ? 'text-amber-400' : i === 1 ? 'text-slate-300' : i === 2 ? 'text-amber-700' : 'text-sentinel-muted'}`}>
                {i + 1}
              </span>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0"
                style={{ backgroundColor: c + '20', color: c, border: `1px solid ${c}30` }}>
                {initials(emp.full_name)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1 gap-2">
                  <span className="text-sm text-sentinel-text truncate">{emp.full_name}</span>
                  <span className="font-mono text-xs text-sentinel-muted shrink-0">{fmtMins(emp.totalWork)}</span>
                </div>
                <div className="h-1.5 bg-navy-900 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, backgroundColor: c }} />
                </div>
              </div>
              <span className="text-xs font-mono text-sentinel-muted shrink-0">{emp.sessionCount} sess.</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}