import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { sessionsAPI } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, ReferenceLine } from 'recharts'
import { format, subDays, subMonths } from 'date-fns'

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+')) return iso
  return iso + 'Z'
}

export default function MySessions() {
  const { theme } = useTheme()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('month')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    sessionsAPI.getMySessions({ limit: 200 })
      .then(r => setSessions(r.data?.sessions || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const now = new Date()
  const filtered = sessions.filter(s => {
    const d = new Date(toUTC(s.start_time))
    if (period === 'week') return d >= subDays(now, 7)
    if (period === 'month') return d >= subMonths(now, 1)
    return true
  })

  // Chart data — daily totals
  const days = period === 'week' ? 7 : period === 'month' ? 30 : 60
  const chartData = Array.from({ length: days }, (_, i) => {
    const d = subDays(now, days - 1 - i)
    const dayStr = format(d, 'yyyy-MM-dd')
    const daySessions = filtered.filter(s => format(new Date(toUTC(s.start_time)), 'yyyy-MM-dd') === dayStr)
    const totalWork = daySessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
    return {
      day: days <= 7 ? format(d, 'EEE').toUpperCase() : format(d, 'dd/MM'),
      minutes: totalWork,
      hours: +(totalWork / 60).toFixed(1),
    }
  }).filter(d => days <= 30 || d.minutes > 0)

  const totalWork = filtered.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
  const totalBreak = filtered.reduce((a, s) => a + (s.total_break_minutes || 0), 0)
  const completed = filtered.filter(s => s.status === 'completed').length
  const avgWork = filtered.length ? Math.round(totalWork / filtered.length) : 0

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '10px 14px' }}>
        <div style={{ fontSize: '10px', color: theme.textMuted, letterSpacing: '1px', marginBottom: '4px' }}>{label}</div>
        <div style={{ fontSize: '14px', fontWeight: '900', color: theme.accent }}>
          {Math.floor(payload[0].value / 60)}h {payload[0].value % 60}m
        </div>
      </div>
    )
  }

  const statusColor = {
    completed: theme.success,
    partial: theme.warning,
    active: theme.info,
    incomplete: theme.danger,
    abandoned: theme.textMuted,
  }

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.accent, fontWeight: '700', marginBottom: '8px' }}>WORK HISTORY</div>
        <div style={{ fontSize: '32px', fontWeight: '900', letterSpacing: '-2px', color: theme.text }}>MY SESSIONS.</div>
      </div>

      {/* Period filter */}
      <div style={{ display: 'flex', gap: '0', marginBottom: '24px', border: `2px solid ${theme.border}`, width: 'fit-content' }}>
        {[['week','7 DAYS'],['month','30 DAYS'],['all','ALL TIME']].map(([val, label]) => (
          <div
            key={val}
            onClick={() => setPeriod(val)}
            style={{
              padding: '10px 20px',
              fontSize: '9px',
              letterSpacing: '2px',
              fontWeight: '700',
              cursor: 'pointer',
              background: period === val ? theme.accent : 'transparent',
              color: period === val ? '#fff' : theme.textMuted,
              borderRight: val !== 'all' ? `2px solid ${theme.border}` : 'none',
            }}
          >
            {label}
          </div>
        ))}
      </div>

      {/* Summary stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0', marginBottom: '24px', border: `2px solid ${theme.border}` }}>
        {[
          { label: 'TOTAL WORK', value: `${Math.floor(totalWork / 60)}H ${totalWork % 60}M`, color: theme.accent },
          { label: 'SESSIONS', value: filtered.length, color: theme.text },
          { label: 'COMPLETED', value: completed, color: theme.success },
          { label: 'AVG / DAY', value: `${Math.floor(avgWork / 60)}H ${avgWork % 60}M`, color: theme.text },
        ].map((s, i) => (
          <div key={i} style={{ padding: '20px', background: theme.card, borderRight: i < 3 ? `2px solid ${theme.border}` : 'none' }}>
            <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700', marginBottom: '8px' }}>{s.label}</div>
            <div style={{ fontSize: '26px', fontWeight: '900', letterSpacing: '-1px', color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '20px', marginBottom: '24px' }}>
        <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.textMuted, fontWeight: '700', marginBottom: '16px' }}>DAILY WORK HOURS</div>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={chartData} barSize={period === 'week' ? 32 : 12}>
            <XAxis dataKey="day" tick={{ fill: theme.textMuted, fontSize: 9, fontFamily: 'monospace', letterSpacing: 1 }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={400} stroke={theme.border} strokeDasharray="4 4" />
            <Bar dataKey="minutes" fill={theme.accent} radius={0} />
          </BarChart>
        </ResponsiveContainer>
        <div style={{ fontSize: '9px', color: theme.textMuted, marginTop: '8px', letterSpacing: '1px' }}>
          DASHED LINE = 6H 40M DAILY TARGET
        </div>
      </div>

      {/* Session list */}
      <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.textMuted, fontWeight: '700', marginBottom: '16px' }}>
        SESSION LOG — {filtered.length} RECORDS
      </div>

      {loading ? (
        <div style={{ color: theme.textMuted, fontSize: '11px', letterSpacing: '2px' }}>LOADING...</div>
      ) : (
        <div style={{ background: theme.card, border: `2px solid ${theme.border}` }}>
          {filtered.length === 0 && (
            <div style={{ padding: '40px', textAlign: 'center', fontSize: '10px', color: theme.textMuted, letterSpacing: '1px' }}>
              NO SESSIONS IN THIS PERIOD
            </div>
          )}
          {[...filtered].sort((a, b) => new Date(toUTC(b.start_time)) - new Date(toUTC(a.start_time))).map((s, i) => {
            const isExp = expanded === s.id
            const start = new Date(toUTC(s.start_time))
            const end = s.end_time ? new Date(toUTC(s.end_time)) : null
            const dur = end ? Math.round((end - start) / 60000) : null
            const sc = statusColor[s.status] || theme.textMuted

            return (
              <div key={s.id} style={{ borderBottom: i < filtered.length - 1 ? `1px solid ${theme.border}` : 'none' }}>
                <div
                  onClick={() => setExpanded(isExp ? null : s.id)}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', cursor: 'pointer' }}
                >
                  <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                    <div style={{ width: '4px', alignSelf: 'stretch', background: sc, flexShrink: 0 }} />
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: '700', color: theme.text }}>
                        {format(start, 'EEEE, dd MMMM yyyy').toUpperCase()}
                      </div>
                      <div style={{ fontSize: '10px', color: theme.textMuted, marginTop: '3px' }}>
                        {format(start, 'HH:mm')} → {end ? format(end, 'HH:mm') : 'ONGOING'}
                        {dur && ` · ${Math.floor(dur/60)}h ${dur%60}m total`}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '16px', fontWeight: '900', color: theme.text }}>{s.total_work_minutes || 0}m</div>
                      <div style={{ fontSize: '9px', color: theme.textMuted, letterSpacing: '1px' }}>WORKED</div>
                    </div>
                    <div style={{ fontSize: '9px', letterSpacing: '1px', fontWeight: '700', color: sc, background: sc + '20', padding: '6px 12px' }}>
                      {s.status?.toUpperCase()}
                    </div>
                    <div style={{ fontSize: '12px', color: theme.textMuted }}>{isExp ? '▲' : '▼'}</div>
                  </div>
                </div>

                {isExp && (
                  <div style={{ padding: '0 20px 20px 40px', background: theme.surface }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0', border: `2px solid ${theme.border}` }}>
                      {[
                        { label: 'WORK TIME', value: `${s.total_work_minutes || 0}m` },
                        { label: 'BREAK TIME', value: `${s.total_break_minutes || 0}m` },
                        { label: 'LUNCH', value: s.lunch_taken ? 'YES' : 'NO' },
                        { label: 'QUALITY', value: s.session_quality_score ? `${Math.round(s.session_quality_score)}%` : '—' },
                      ].map((item, j) => (
                        <div key={j} style={{ padding: '12px 16px', background: theme.card, borderRight: j < 3 ? `2px solid ${theme.border}` : 'none' }}>
                          <div style={{ fontSize: '9px', letterSpacing: '1px', color: theme.textMuted, fontWeight: '700', marginBottom: '4px' }}>{item.label}</div>
                          <div style={{ fontSize: '16px', fontWeight: '900', color: theme.text }}>{item.value}</div>
                        </div>
                      ))}
                    </div>
                    {s.risk_score > 0 && (
                      <div style={{ marginTop: '8px', padding: '10px 14px', background: theme.danger + '15', border: `1px solid ${theme.danger}`, fontSize: '10px', color: theme.danger }}>
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
