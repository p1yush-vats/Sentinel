import { useEffect, useState } from 'react'
import { employeesAPI, sessionsAPI, metricsAPI } from '../services/api'
import { fmtMins, deptColor, initials } from '../utils/helpers'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts'

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

const DEPT_COLORS = ['#22d3ee', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#f97316']

export default function Analytics() {
  const [employees,   setEmployees]   = useState([])
  const [sessions,    setSessions]    = useState([])
  const [deptStats,   setDeptStats]   = useState([])
  const [topWorkers,  setTopWorkers]  = useState([])
  const [loading,     setLoading]     = useState(true)
  const [period,      setPeriod]      = useState('week')

  useEffect(() => {
    Promise.all([
      employeesAPI.getAll({ limit: 200 }),
      sessionsAPI.getAll({ limit: 500 }),
    ]).then(([empRes, sessRes]) => {
      const emps  = empRes.data?.employees || []
      const sess  = sessRes.data?.sessions  || []

      setEmployees(emps)
      setSessions(sess)

      // Department breakdown
      const depts = {}
      emps.forEach(e => {
        if (!e.department) return
        if (!depts[e.department]) depts[e.department] = { name: e.department, employees: 0, avgWork: 0, totalWork: 0 }
        depts[e.department].employees++
      })
      sess.forEach(s => {
        const emp = emps.find(e => e.id === s.employee_id)
        if (!emp?.department || !depts[emp.department]) return
        depts[emp.department].totalWork += (s.total_work_minutes || 0)
      })
      Object.values(depts).forEach(d => {
        d.avgWork = d.employees > 0 ? Math.round(d.totalWork / d.employees) : 0
      })
      setDeptStats(Object.values(depts))

      // Top workers by total work minutes
      const empWork = {}
      emps.forEach(e => { empWork[e.id] = { ...e, totalWork: 0, sessions: 0 } })
      sess.forEach(s => {
        if (empWork[s.employee_id]) {
          empWork[s.employee_id].totalWork += (s.total_work_minutes || 0)
          empWork[s.employee_id].sessions++
        }
      })
      const sorted = Object.values(empWork)
        .filter(e => e.totalWork > 0)
        .sort((a, b) => b.totalWork - a.totalWork)
        .slice(0, 8)
      setTopWorkers(sorted)
    })
    .catch(() => {})
    .finally(() => setLoading(false))
  }, [])

  // Session status distribution for pie
  const statusDist = [
    { name: 'Completed', value: sessions.filter(s => s.status === 'completed').length, color: '#10b981' },
    { name: 'Active',    value: sessions.filter(s => s.status === 'active').length,    color: '#22d3ee' },
    { name: 'Partial',   value: sessions.filter(s => s.status === 'partial').length,   color: '#f59e0b' },
    { name: 'Flagged',   value: sessions.filter(s => s.status === 'flagged').length,   color: '#ef4444' },
    { name: 'Abandoned', value: sessions.filter(s => s.status === 'abandoned').length, color: '#64748b' },
  ].filter(d => d.value > 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <h1 className="font-display font-bold text-2xl text-sentinel-text">Analytics</h1>
          <p className="text-sentinel-muted text-sm font-mono mt-1">Workforce performance overview</p>
        </div>
        <div className="flex gap-2">
          {['week', 'month', 'all'].map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all duration-200
                ${period === p ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20' : 'text-sentinel-muted border-sentinel-border hover:text-sentinel-text'}`}>
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="glow-line" />

      {/* Dept avg work + session dist */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 card p-5 animate-fade-in stagger-1">
          <h3 className="section-title mb-5">Avg Work Minutes by Department</h3>
          {loading ? (
            <div className="h-48 bg-navy-700 rounded animate-pulse" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={deptStats} barSize={28}>
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'IBM Plex Mono' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="avgWork" name="Avg Work (min)" radius={[4, 4, 0, 0]}>
                  {deptStats.map((_, i) => (
                    <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} opacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card p-5 animate-fade-in stagger-2">
          <h3 className="section-title mb-5">Session Distribution</h3>
          {loading ? (
            <div className="h-48 bg-navy-700 rounded animate-pulse" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={statusDist} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                  {statusDist.map((entry, i) => (
                    <Cell key={i} fill={entry.color} opacity={0.85} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 11, fontFamily: 'IBM Plex Mono' }}>{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Top workers leaderboard */}
      <div className="card p-5 animate-fade-in stagger-3">
        <h3 className="section-title mb-5">Top Performers</h3>
        {loading ? (
          Array(5).fill(0).map((_, i) => (
            <div key={i} className="flex items-center gap-4 py-3 border-b border-sentinel-border/30">
              <div className="w-6 h-6 bg-navy-700 rounded animate-pulse" />
              <div className="flex-1 h-4 bg-navy-700 rounded animate-pulse" />
            </div>
          ))
        ) : topWorkers.map((emp, i) => {
          const maxWork = topWorkers[0]?.totalWork || 1
          const pct = (emp.totalWork / maxWork) * 100
          return (
            <div key={emp.id} className={`flex items-center gap-4 py-3 border-b border-sentinel-border/30 last:border-0 animate-fade-in stagger-${Math.min(i+1,5)}`}>
              <span className={`font-mono font-bold text-sm w-6 text-center ${i === 0 ? 'text-amber-400' : i === 1 ? 'text-slate-300' : i === 2 ? 'text-amber-700' : 'text-sentinel-muted'}`}>
                {i + 1}
              </span>
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-bold shrink-0"
                style={{ backgroundColor: deptColor(emp.department) + '20', color: deptColor(emp.department), border: `1px solid ${deptColor(emp.department)}30` }}>
                {initials(emp.full_name)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-sentinel-text truncate">{emp.full_name}</span>
                  <span className="font-mono text-xs text-sentinel-muted ml-4 shrink-0">{fmtMins(emp.totalWork)}</span>
                </div>
                <div className="h-1.5 bg-navy-900 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, backgroundColor: deptColor(emp.department) }} />
                </div>
              </div>
              <span className="text-xs font-mono text-sentinel-muted shrink-0">{emp.sessions}s</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
