import { useEffect, useState, useCallback } from 'react'
import { sessionsAPI, employeesAPI } from '../services/api'
import { fmt, fmtMins, statusBadge, initials, deptColor } from '../utils/helpers'
import { Search, Clock, Filter, X, Radio } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const STATUSES = ['all', 'active', 'completed', 'flagged', 'partial', 'abandoned']

export default function Sessions() {
  const navigate = useNavigate()
  const [sessions,    setSessions]    = useState([])
  const [employees,   setEmployees]   = useState({})
  const [loading,     setLoading]     = useState(true)
  const [status,      setStatus]      = useState('all')
  const [search,      setSearch]      = useState('')
  const [dateFrom,    setDateFrom]    = useState('')
  const [dateTo,      setDateTo]      = useState('')
  const [showFilter,  setShowFilter]  = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)

  // Employee map — fetch once
  useEffect(() => {
    employeesAPI.getAll({ limit: 500 })
      .then(r => {
        const map = {}
        ;(r.data?.employees || []).forEach(e => { map[e.id] = e })
        setEmployees(map)
      })
      .catch(() => {})
  }, [])

  // Fetch sessions — silent=true skips the loading spinner (for auto-refresh)
  const fetchSessions = useCallback((silent = false) => {
    if (!silent) setLoading(true)
    const params = { limit: 200 }
    if (status !== 'all') params.status = status
    sessionsAPI.getAll(params)
      .then(r => {
        setSessions(r.data?.sessions || [])
        setLastRefresh(new Date())
      })
      .catch(() => {})
      .finally(() => { if (!silent) setLoading(false) })
  }, [status])

  // Load on mount + when status filter changes
  useEffect(() => { fetchSessions(false) }, [fetchSessions])

  // Auto-refresh every 60s silently — picks up synced work minutes from desktop app
  useEffect(() => {
    const id = setInterval(() => fetchSessions(true), 60000)
    return () => clearInterval(id)
  }, [fetchSessions])

  // Client-side filtering
  const filtered = sessions.filter(s => {
    if (search) {
      const emp = employees[s.employee_id]
      const hay = [s.id, emp?.full_name, emp?.email, emp?.department]
        .filter(Boolean).join(' ').toLowerCase()
      if (!hay.includes(search.toLowerCase())) return false
    }
    const toDate = (raw) => raw ? new Date(raw.includes('Z') || raw.includes('+') ? raw : raw + 'Z') : null
    const dt = toDate(s.start_time)
    if (dt && dateFrom && dt < new Date(dateFrom)) return false
    if (dt && dateTo) {
      const to = new Date(dateTo); to.setDate(to.getDate() + 1)
      if (dt > to) return false
    }
    return true
  })

  const clearFilters = () => { setSearch(''); setDateFrom(''); setDateTo(''); setStatus('all') }
  const hasActiveFilters = search || dateFrom || dateTo || status !== 'all'
  const activeCount = sessions.filter(s => s.status === 'active').length

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <h1 className="font-display font-bold text-2xl text-sentinel-text">Sessions</h1>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            <p className="text-sentinel-muted text-sm font-mono">
              {filtered.length} of {sessions.length} sessions
            </p>
            {activeCount > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-mono text-emerald-400">
                  {activeCount} live · syncs every 60s
                </span>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => fetchSessions(false)}
            className="btn-ghost text-xs flex items-center gap-1.5">
            <Radio size={13} /> Refresh
          </button>
          <button onClick={() => setShowFilter(f => !f)}
            className={`btn-ghost flex items-center gap-2 text-sm ${showFilter ? 'border-cyan-400/40 text-cyan-400' : ''}`}>
            <Filter size={14} /> Filters
            {hasActiveFilters && <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0" />}
          </button>
        </div>
      </div>

      <div className="glow-line" />

      {/* Search + status pills */}
      <div className="space-y-3 animate-fade-in stagger-1">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-sentinel-muted" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by employee name, email, or session ID…"
            className="input-field pl-9 pr-9" />
          {search && (
            <button onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-sentinel-muted hover:text-sentinel-text">
              <X size={14} />
            </button>
          )}
        </div>

        <div className="flex gap-2 flex-wrap">
          {STATUSES.map(s => (
            <button key={s} onClick={() => setStatus(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all capitalize
                ${status === s ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20' : 'text-sentinel-muted border-sentinel-border hover:text-sentinel-text'}`}>
              {s}
              {s === 'active' && activeCount > 0 && (
                <span className="ml-1.5 bg-emerald-400/20 text-emerald-400 text-[9px] px-1 py-0.5 rounded-full">
                  {activeCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {showFilter && (
          <div className="flex flex-wrap gap-3 items-center p-4 bg-navy-800 rounded-xl border border-sentinel-border animate-fade-in">
            <div>
              <p className="label mb-1">From</p>
              <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                className="input-field w-auto text-sm" />
            </div>
            <div>
              <p className="label mb-1">To</p>
              <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
                className="input-field w-auto text-sm" />
            </div>
            {hasActiveFilters && (
              <button onClick={clearFilters} className="mt-5 btn-ghost text-xs flex items-center gap-1.5">
                <X size={12} /> Clear all
              </button>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-hidden animate-fade-in stagger-2">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-sentinel-border">
                <th className="label text-left px-5 py-3">Employee</th>
                <th className="label text-left px-5 py-3 hidden sm:table-cell">Started</th>
                <th className="label text-left px-5 py-3">Work</th>
                <th className="label text-left px-5 py-3 hidden md:table-cell">Break</th>
                <th className="label text-left px-5 py-3 hidden lg:table-cell">Lunch</th>
                <th className="label text-left px-5 py-3 hidden lg:table-cell">Risk</th>
                <th className="label text-left px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array(8).fill(0).map((_, i) => (
                  <tr key={i} className="table-row">
                    <td colSpan={7} className="px-5 py-3">
                      <div className="h-4 bg-navy-700 rounded animate-pulse" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center">
                    <p className="text-sentinel-muted font-mono text-sm">No sessions found</p>
                  </td>
                </tr>
              ) : filtered.map(s => {
                const emp      = employees[s.employee_id]
                const color    = deptColor(emp?.department)
                const isActive = s.status === 'active'

                return (
                  <tr key={s.id}
                    onClick={() => emp && navigate(`/employees/${emp.id}`)}
                    className={`table-row cursor-pointer transition-colors
                      ${isActive ? 'bg-emerald-400/[0.02] hover:bg-emerald-400/[0.05]' : 'hover:bg-navy-700/20'}`}>

                    {/* Employee */}
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2.5">
                        {emp?.avatar_url && (
                          <img src={emp.avatar_url} alt={emp.full_name}
                            className="w-7 h-7 rounded-full object-cover shrink-0 border"
                            style={{ borderColor: color + '40' }}
                            onError={e => { e.target.style.display='none' }} />
                        )}
                        {!emp?.avatar_url && (
                          <div className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-mono font-bold shrink-0"
                            style={{ backgroundColor: color + '18', color, border: `1px solid ${color}30` }}>
                            {emp ? initials(emp.full_name) : '??'}
                          </div>
                        )}
                        <div className="min-w-0">
                          <p className="text-sm text-sentinel-text font-medium truncate">
                            {emp?.full_name || 'Unknown'}
                          </p>
                          <p className="text-[11px] font-mono text-sentinel-muted truncate">
                            {emp?.department || s.employee_id?.slice(0, 8) + '…'}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Started */}
                    <td className="px-5 py-3 hidden sm:table-cell">
                      <span className="font-mono text-xs text-sentinel-text">{fmt(s.start_time)}</span>
                    </td>

                    {/* Work — value synced from desktop every ~30s */}
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1.5">
                        {isActive
                          ? <Radio size={11} className="text-emerald-400 shrink-0 animate-pulse" />
                          : <Clock size={12} className="text-cyan-400 shrink-0" />
                        }
                        <span className={`font-mono text-sm ${isActive ? 'text-emerald-400' : 'text-sentinel-text'}`}>
                          {fmtMins(s.total_work_minutes)}
                        </span>
                      </div>
                    </td>

                    {/* Break */}
                    <td className="px-5 py-3 hidden md:table-cell">
                      <span className="font-mono text-sm text-sentinel-muted">
                        {fmtMins(s.total_break_minutes)}
                      </span>
                    </td>

                    {/* Lunch */}
                    <td className="px-5 py-3 hidden lg:table-cell">
                      <span className={`text-xs font-mono ${s.lunch_taken ? 'text-emerald-400' : 'text-sentinel-muted'}`}>
                        {s.lunch_taken ? '✓ taken' : '—'}
                      </span>
                    </td>

                    {/* Risk */}
                    <td className="px-5 py-3 hidden lg:table-cell">
                      <span className={`font-mono text-sm font-bold ${
                        (s.risk_score||0) >= 75 ? 'text-red-400'    :
                        (s.risk_score||0) >= 50 ? 'text-orange-400' :
                        (s.risk_score||0) >= 25 ? 'text-amber-400'  : 'text-emerald-400'
                      }`}>
                        {Math.round(s.risk_score || 0)}
                      </span>
                    </td>

                    {/* Status */}
                    <td className="px-5 py-3">
                      <span className={statusBadge(s.status)}>{s.status}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Footer — last refresh time */}
        {lastRefresh && (
          <div className="px-5 py-2 border-t border-sentinel-border/50 flex items-center justify-between">
            <span className="text-[10px] font-mono text-sentinel-muted">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </span>
            {activeCount > 0 && (
              <span className="text-[10px] font-mono text-emerald-400/60">
                Auto-refreshing every 60s
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}