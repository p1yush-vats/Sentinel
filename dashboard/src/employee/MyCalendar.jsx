import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { useAuthStore } from '../store/authStore'
import { sessionsAPI } from '../services/api'
import api from '../services/api'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isToday, getDay, subMonths, addMonths } from 'date-fns'

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+')) return iso
  return iso + 'Z'
}

export default function MyCalendar() {
  const { theme } = useTheme()
  const { user }  = useAuthStore()
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [sessions,     setSessions]     = useState([])
  const [leaves,       setLeaves]       = useState([])
  const [teamLeaves,   setTeamLeaves]   = useState([])
  const [loading,      setLoading]      = useState(true)
  const [selected,     setSelected]     = useState(null)
  const t = theme

  useEffect(() => {
    Promise.all([
      sessionsAPI.getMySessions({ limit: 200 }),
      api.get('/leaves/'),
      api.get('/leaves/team/').catch(() => ({ data: { leaves: [] } })),
    ]).then(([sRes, lRes, tRes]) => {
      setSessions(sRes.data?.sessions || [])
      setLeaves(lRes.data?.leaves || [])
      setTeamLeaves(tRes.data?.leaves || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const monthStart  = startOfMonth(currentMonth)
  const monthEnd    = endOfMonth(currentMonth)
  const days        = eachDayOfInterval({ start: monthStart, end: monthEnd })
  const startPad    = getDay(monthStart)
  const paddedDays  = [...Array(startPad).fill(null), ...days]

  function getDayData(date) {
    if (!date) return null
    const dayStr    = format(date, 'yyyy-MM-dd')
    const daySess   = sessions.filter(s => format(new Date(toUTC(s.start_time)), 'yyyy-MM-dd') === dayStr)
    const dayLeaves = leaves.filter(l => {
      const d = new Date(dayStr)
      return d >= new Date(l.from_date) && d <= new Date(l.to_date) && l.status === 'approved'
    })
    const dayTeam   = teamLeaves.filter(l => {
      const d = new Date(dayStr)
      return d >= new Date(l.from_date) && d <= new Date(l.to_date) && l.status === 'approved' && l.employee_id !== user?.id
    })
    return { daySessions: daySess, dayLeaves, dayTeamLeaves: dayTeam }
  }

  function getDayStatus(date) {
    if (!date) return null
    const { daySessions, dayLeaves } = getDayData(date)
    const dow = date.getDay()
    if (dow === 0 || dow === 6) return 'weekend'
    if (dayLeaves.length > 0)   return 'leave'
    if (daySessions.length > 0) {
      const total = daySessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
      return total >= 360 ? 'full' : 'partial'
    }
    if (date > new Date()) return 'future'
    return 'absent'
  }

  const statusConfig = {
    full:    { bg: t.success,                   label: 'Full Day',  color: '#fff' },
    partial: { bg: t.warning,                   label: 'Partial',   color: '#000' },
    leave:   { bg: t.info,                      label: 'On Leave',  color: '#fff' },
    absent:  { bg: (t.danger || '#ff4444') + '25', label: 'Absent', color: t.danger || '#ff4444' },
    weekend: { bg: t.surface,                   label: 'Weekend',   color: t.textMuted },
    future:  { bg: 'transparent',               label: 'Upcoming',  color: t.textMuted },
  }

  const selectedData = selected ? getDayData(selected) : null

  const monthlySummary = [
    { label: 'PRESENT', value: days.filter(d => getDayStatus(d) === 'full').length,    color: t.success },
    { label: 'PARTIAL', value: days.filter(d => getDayStatus(d) === 'partial').length, color: t.warning },
    { label: 'ON LEAVE',value: days.filter(d => getDayStatus(d) === 'leave').length,   color: t.info },
    { label: 'ABSENT',  value: days.filter(d => getDayStatus(d) === 'absent').length,  color: t.danger },
  ]

  return (
    <div>
      <style>{`
        .cal-layout { display: grid; grid-template-columns: 1fr; gap: 20px; }
        .cal-summary { display: grid; grid-template-columns: repeat(4,1fr); gap:0; margin-top:16px; border:2px solid ${t.border}; }
        .cal-legend  { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
        @media (min-width: 860px) { .cal-layout { grid-template-columns: 1fr 280px; } }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 9, letterSpacing: '3px', color: t.accent, fontWeight: 700, marginBottom: 6 }}>ATTENDANCE & LEAVE</div>
        <div style={{ fontSize: 'clamp(22px, 6vw, 32px)', fontWeight: 900, letterSpacing: '-2px', color: t.text }}>CALENDAR.</div>
      </div>

      {/* Legend */}
      <div className="cal-legend">
        {Object.entries(statusConfig).filter(([k]) => k !== 'future').map(([key, val]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 10, height: 10, background: val.bg, border: `1px solid ${t.border}`, flexShrink: 0 }} />
            <span style={{ fontSize: 8, letterSpacing: '1px', color: t.textMuted, fontWeight: 700 }}>{val.label.toUpperCase()}</span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <div style={{ width: 10, height: 10, background: (t.info || '#0088ff') + '30', border: `2px solid ${t.info}`, flexShrink: 0 }} />
          <span style={{ fontSize: 8, letterSpacing: '1px', color: t.textMuted, fontWeight: 700 }}>TEAM ON LEAVE</span>
        </div>
      </div>

      <div className="cal-layout">
        {/* Calendar */}
        <div>
          {/* Month nav */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <button onClick={() => setCurrentMonth(m => subMonths(m, 1))}
              style={{ background: 'transparent', border: `2px solid ${t.border}`, color: t.text, padding: '7px 14px', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', fontWeight: 700 }}>
              ←
            </button>
            <div style={{ fontSize: 13, fontWeight: 900, letterSpacing: '2px', color: t.text }}>
              {format(currentMonth, 'MMMM yyyy').toUpperCase()}
            </div>
            <button onClick={() => setCurrentMonth(m => addMonths(m, 1))}
              style={{ background: 'transparent', border: `2px solid ${t.border}`, color: t.text, padding: '7px 14px', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', fontWeight: 700 }}>
              →
            </button>
          </div>

          {/* Day headers */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: 2, marginBottom: 2 }}>
            {['S','M','T','W','T','F','S'].map((d, i) => (
              <div key={i} style={{ textAlign: 'center', fontSize: 8, letterSpacing: '1px', fontWeight: 700, color: t.textMuted, padding: '6px 0' }}>{d}</div>
            ))}
          </div>

          {/* Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7,1fr)', gap: 2 }}>
            {paddedDays.map((date, i) => {
              if (!date) return <div key={`pad-${i}`} />
              const status  = getDayStatus(date)
              const cfg     = statusConfig[status] || statusConfig.future
              const data    = getDayData(date)
              const today   = isToday(date)
              const isSel   = selected && format(selected,'yyyy-MM-dd') === format(date,'yyyy-MM-dd')
              const hasTeam = data?.dayTeamLeaves?.length > 0

              return (
                <div
                  key={date.toISOString()}
                  onClick={() => setSelected(date)}
                  style={{
                    aspectRatio: '1',
                    background: cfg.bg,
                    border: isSel
                      ? `2px solid ${t.accent}`
                      : today
                        ? `2px solid ${t.text}`
                        : hasTeam
                          ? `2px solid ${t.info}`
                          : `1px solid ${t.border}`,
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center',
                    cursor: 'pointer', position: 'relative',
                  }}
                >
                  <span style={{ fontSize: 'clamp(9px, 2vw, 11px)', fontWeight: today ? 900 : 700, color: cfg.color }}>
                    {format(date, 'd')}
                  </span>
                  {data?.daySessions?.length > 0 && (
                    <div style={{ width: 3, height: 3, background: cfg.color, borderRadius: '50%', marginTop: 1, opacity: 0.7 }} />
                  )}
                  {hasTeam && (
                    <div style={{ position: 'absolute', top: 2, right: 2, width: 3, height: 3, background: t.info, borderRadius: '50%' }} />
                  )}
                </div>
              )
            })}
          </div>

          {/* Monthly summary */}
          <div className="cal-summary">
            {monthlySummary.map((s, i) => (
              <div key={i} style={{ padding: '12px 8px', borderRight: i < 3 ? `2px solid ${t.border}` : 'none', background: t.card, textAlign: 'center' }}>
                <div style={{ fontSize: 'clamp(18px, 4vw, 22px)', fontWeight: 900, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 7, letterSpacing: '1.5px', color: t.textMuted, marginTop: 3 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Day detail panel */}
        <div>
          <div style={{ fontSize: 8, letterSpacing: '3px', color: t.textMuted, fontWeight: 700, marginBottom: 14 }}>
            {selected ? format(selected, 'EEEE, dd MMMM').toUpperCase() : 'SELECT A DAY'}
          </div>

          {selected && selectedData ? (
            <div>
              {/* Sessions */}
              <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: 14, marginBottom: 10 }}>
                <div style={{ fontSize: 8, letterSpacing: '2px', color: t.textMuted, fontWeight: 700, marginBottom: 10 }}>MY SESSIONS</div>
                {selectedData.daySessions.length === 0 ? (
                  <div style={{ fontSize: 10, color: t.textMuted }}>No sessions this day</div>
                ) : selectedData.daySessions.map(s => (
                  <div key={s.id} style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: t.text }}>{s.total_work_minutes || 0} min worked</div>
                    <div style={{ fontSize: 9, color: t.textMuted }}>{s.total_break_minutes || 0} min break · {s.status}</div>
                  </div>
                ))}
              </div>

              {selectedData.dayLeaves.length > 0 && (
                <div style={{ background: t.card, border: `2px solid ${t.info}`, padding: 14, marginBottom: 10 }}>
                  <div style={{ fontSize: 8, letterSpacing: '2px', color: t.info, fontWeight: 700, marginBottom: 8 }}>ON LEAVE</div>
                  {selectedData.dayLeaves.map((l, i) => (
                    <div key={i} style={{ fontSize: 11, color: t.text }}>{l.leave_type} — {l.reason}</div>
                  ))}
                </div>
              )}

              {selectedData.dayTeamLeaves.length > 0 && (
                <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: 14 }}>
                  <div style={{ fontSize: 8, letterSpacing: '2px', color: t.textMuted, fontWeight: 700, marginBottom: 10 }}>
                    TEAM ON LEAVE ({selectedData.dayTeamLeaves.length})
                  </div>
                  {selectedData.dayTeamLeaves.map((l, i) => (
                    <div key={i} style={{ fontSize: 10, color: t.textSub, marginBottom: 5, display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                      <span>{l.employee_name || 'Team member'}</span>
                      <span style={{ color: t.info }}>{l.leave_type}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: 28, textAlign: 'center' }}>
              <div style={{ fontSize: 22, color: t.border, marginBottom: 8 }}>▦</div>
              <div style={{ fontSize: 9, color: t.textMuted, letterSpacing: '1px' }}>CLICK ANY DAY TO VIEW DETAILS</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}