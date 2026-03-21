import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { sessionsAPI } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { format, subDays, subMonths } from 'date-fns'

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+')) return iso
  return iso + 'Z'
}

export default function MySessions() {
  const { theme } = useTheme()
  const [sessions,  setSessions]  = useState([])
  const [loading,   setLoading]   = useState(true)
  const [period,    setPeriod]    = useState('month')
  const [expanded,  setExpanded]  = useState(null)
  const t = theme

  useEffect(() => {
    sessionsAPI.getMySessions({ limit: 200 })
      .then(r => setSessions(r.data?.sessions || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const now = new Date()
  const filtered = sessions.filter(s => {
    const d = new Date(toUTC(s.start_time))
    if (period === 'week')  return d >= subDays(now, 7)
    if (period === 'month') return d >= subMonths(now, 1)
    return true
  })

  const days = period === 'week' ? 7 : period === 'month' ? 30 : 60
  const chartData = Array.from({ length: days }, (_, i) => {
    const d      = subDays(now, days - 1 - i)
    const dayStr = format(d, 'yyyy-MM-dd')
    const total  = filtered
      .filter(s => format(new Date(toUTC(s.start_time)), 'yyyy-MM-dd') === dayStr)
      .reduce((a, s) => a + (s.total_work_minutes || 0), 0)
    return {
      day: days <= 7 ? format(d, 'EEE').toUpperCase() : format(d, 'dd/MM'),
      minutes: total,
    }
  }).filter(d => days <= 30 || d.minutes > 0)

  const totalWork = filtered.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
  const completed = filtered.filter(s => s.status === 'completed').length
  const avgWork   = filtered.length ? Math.round(totalWork / filtered.length) : 0

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: '8px 12px' }}>
        <div style={{ fontSize: 9, color: t.textMuted, letterSpacing: '1px', marginBottom: 3 }}>{label}</div>
        <div style={{ fontSize: 13, fontWeight: 900, color: t.accent }}>
          {Math.floor(payload[0].value / 60)}h {payload[0].value % 60}m
        </div>
      </div>
    )
  }

  const statusColor = {
    completed: t.success, partial: t.warning,
    active: t.info, abandoned: t.textMuted,
  }

  return (
    <div>
      <style>{`
        .sess-grid-4 { display: grid; grid-template-columns: repeat(2, 1fr); }
        .sess-detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); }
        @media (min-width: 600px) {
          .sess-grid-4 { grid-template-columns: repeat(4, 1fr); }
          .sess-detail-grid { grid-template-columns: repeat(4, 1fr); }
        }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 9, letterSpacing: '3px', color: t.accent, fontWeight: 700, marginBottom: 6 }}>WORK HISTORY</div>
        <div style={{ fontSize: 'clamp(22px, 6vw, 32px)', fontWeight: 900, letterSpacing: '-2px', color: t.text }}>MY SESSIONS.</div>
      </div>

      {/* Period filter — scrollable on mobile */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, border: `2px solid ${t.border}`, width: 'fit-content', overflowX: 'auto' }}>
        {[['week','7 DAYS'],['month','30 DAYS'],['all','ALL TIME']].map(([val, label]) => (
          <div key={val} onClick={() => setPeriod(val)} style={{
            padding: '9px 16px', fontSize: 9, letterSpacing: '2px', fontWeight: 700, cursor: 'pointer',
            background: period === val ? t.accent : 'transparent',
            color: period === val ? '#fff' : t.textMuted,
            borderRight: val !== 'all' ? `2px solid ${t.border}` : 'none',
            whiteSpace: 'nowrap',
          }}>
            {label}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="sess-grid-4" style={{ marginBottom: 20, border: `2px solid ${t.border}` }}>
        {[
          { label: 'TOTAL WORK',  value: `${Math.floor(totalWork/60)}H ${totalWork%60}M`, color: t.accent },
          { label: 'SESSIONS',    value: filtered.length,  color: t.text },
          { label: 'COMPLETED',   value: completed,        color: t.success },
          { label: 'AVG / DAY',   value: `${Math.floor(avgWork/60)}H ${avgWork%60}M`, color: t.text },
        ].map((s, i) => (
          <div key={i} style={{ padding: '14px 12px', background: t.card, borderRight: i < 3 ? `2px solid ${t.border}` : 'none' }}>
            <div style={{ fontSize: 8, letterSpacing: '2px', color: t.textMuted, fontWeight: 700, marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 'clamp(18px, 4vw, 24px)', fontWeight: 900, letterSpacing: '-1px', color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: '16px 12px', marginBottom: 20 }}>
        <div style={{ fontSize: 9, letterSpacing: '3px', color: t.textMuted, fontWeight: 700, marginBottom: 12 }}>DAILY WORK HOURS</div>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={chartData} barSize={period === 'week' ? 28 : 10}>
            <XAxis dataKey="day" tick={{ fill: t.textMuted, fontSize: 8, fontFamily: 'monospace', letterSpacing: 1 }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={400} stroke={t.border} strokeDasharray="4 4" />
            <Bar dataKey="minutes" fill={t.accent} radius={0} />
          </BarChart>
        </ResponsiveContainer>
        <div style={{ fontSize: 8, color: t.textMuted, marginTop: 8, letterSpacing: '1px' }}>
          DASHED LINE = 6H 40M DAILY TARGET
        </div>
      </div>

      {/* Session log */}
      <div style={{ fontSize: 9, letterSpacing: '3px', color: t.textMuted, fontWeight: 700, marginBottom: 12 }}>
        SESSION LOG — {filtered.length} RECORDS
      </div>

      {loading ? (
        <div style={{ color: t.textMuted, fontSize: 11, letterSpacing: '2px' }}>LOADING...</div>
      ) : (
        <div style={{ background: t.card, border: `2px solid ${t.border}` }}>
          {filtered.length === 0 && (
            <div style={{ padding: 32, textAlign: 'center', fontSize: 10, color: t.textMuted, letterSpacing: '1px' }}>NO SESSIONS IN THIS PERIOD</div>
          )}
          {[...filtered]
            .sort((a, b) => new Date(toUTC(b.start_time)) - new Date(toUTC(a.start_time)))
            .map((s, i) => {
              const isExp = expanded === s.id
              const start = new Date(toUTC(s.start_time))
              const end   = s.end_time ? new Date(toUTC(s.end_time)) : null
              const dur   = end ? Math.round((end - start) / 60000) : null
              const sc    = statusColor[s.status] || t.textMuted

              return (
                <div key={s.id} style={{ borderBottom: i < filtered.length - 1 ? `1px solid ${t.border}` : 'none' }}>
                  {/* Row header */}
                  <div
                    onClick={() => setExpanded(isExp ? null : s.id)}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 16px', cursor: 'pointer', gap: 8 }}
                  >
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center', minWidth: 0 }}>
                      <div style={{ width: 4, alignSelf: 'stretch', background: sc, flexShrink: 0 }} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: t.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {format(start, 'EEE, dd MMM yyyy').toUpperCase()}
                        </div>
                        <div style={{ fontSize: 9, color: t.textMuted, marginTop: 2 }}>
                          {format(start, 'HH:mm')} → {end ? format(end, 'HH:mm') : 'ONGOING'}
                          {dur ? ` · ${Math.floor(dur/60)}h ${dur%60}m` : ''}
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: 15, fontWeight: 900, color: t.text }}>{s.total_work_minutes || 0}m</div>
                        <div style={{ fontSize: 8, color: t.textMuted, letterSpacing: '1px' }}>WORKED</div>
                      </div>
                      <div style={{ fontSize: 8, letterSpacing: '1px', fontWeight: 700, color: sc, background: sc + '20', padding: '4px 8px', whiteSpace: 'nowrap' }}>
                        {s.status?.toUpperCase()}
                      </div>
                      <div style={{ fontSize: 11, color: t.textMuted }}>{isExp ? '▲' : '▼'}</div>
                    </div>
                  </div>

                  {/* Expanded detail */}
                  {isExp && (
                    <div style={{ padding: '0 16px 16px 28px', background: t.surface }}>
                      <div className="sess-detail-grid" style={{ border: `2px solid ${t.border}` }}>
                        {[
                          { label: 'WORK',    value: `${s.total_work_minutes || 0}m` },
                          { label: 'BREAK',   value: `${s.total_break_minutes || 0}m` },
                          { label: 'LUNCH',   value: s.lunch_taken ? 'YES' : 'NO' },
                          { label: 'QUALITY', value: s.session_quality_score ? `${Math.round(s.session_quality_score)}%` : '—' },
                        ].map((item, j) => (
                          <div key={j} style={{ padding: '10px 12px', background: t.card, borderRight: j % 2 === 0 ? `2px solid ${t.border}` : 'none', borderBottom: j < 2 ? `2px solid ${t.border}` : 'none' }}>
                            <div style={{ fontSize: 8, letterSpacing: '1px', color: t.textMuted, fontWeight: 700, marginBottom: 3 }}>{item.label}</div>
                            <div style={{ fontSize: 15, fontWeight: 900, color: t.text }}>{item.value}</div>
                          </div>
                        ))}
                      </div>
                      {(s.risk_score || 0) > 0 && (
                        <div style={{ marginTop: 8, padding: '8px 12px', background: t.danger + '15', border: `1px solid ${t.danger}`, fontSize: 10, color: t.danger }}>
                          RISK SCORE: {Math.round(s.risk_score)}/100 — {s.risk_score < 25 ? 'LOW RISK' : s.risk_score < 50 ? 'MEDIUM RISK' : 'HIGH RISK'}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}