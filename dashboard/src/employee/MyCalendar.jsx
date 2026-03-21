import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { useAuthStore } from '../store/authStore'
import { sessionsAPI } from '../services/api'
import api from '../services/api'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, getDay, subMonths, addMonths } from 'date-fns'

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+')) return iso
  return iso + 'Z'
}

export default function MyCalendar() {
  const { theme } = useTheme()
  const { user } = useAuthStore()
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [sessions, setSessions] = useState([])
  const [leaves, setLeaves] = useState([])
  const [teamLeaves, setTeamLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

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

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd })

  // Pad start
  const startPad = getDay(monthStart) // 0=Sun
  const paddedDays = [...Array(startPad).fill(null), ...days]

  function getDayData(date) {
    if (!date) return null
    const dayStr = format(date, 'yyyy-MM-dd')

    const daySessions = sessions.filter(s => {
      const st = new Date(toUTC(s.start_time))
      return format(st, 'yyyy-MM-dd') === dayStr
    })

    const dayLeaves = leaves.filter(l => {
      const from = new Date(l.from_date)
      const to = new Date(l.to_date)
      const d = new Date(dayStr)
      return d >= from && d <= to && l.status === 'approved'
    })

    const dayTeamLeaves = teamLeaves.filter(l => {
      const from = new Date(l.from_date)
      const to = new Date(l.to_date)
      const d = new Date(dayStr)
      return d >= from && d <= to && l.status === 'approved' && l.employee_id !== user?.id
    })

    return { daySessions, dayLeaves, dayTeamLeaves }
  }

  function getDayStatus(date) {
    if (!date) return null
    const data = getDayData(date)
    if (!data) return null
    const { daySessions, dayLeaves } = data
    const dow = date.getDay()
    if (dow === 0 || dow === 6) return 'weekend'
    if (dayLeaves.length > 0) return 'leave'
    if (daySessions.length > 0) {
      const totalWork = daySessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
      if (totalWork >= 360) return 'full'
      if (totalWork >= 120) return 'partial'
      return 'partial'
    }
    if (date > new Date()) return 'future'
    return 'absent'
  }

  const statusConfig = {
    full:    { bg: theme.success, label: 'Full Day', color: '#fff' },
    partial: { bg: theme.warning, label: 'Partial', color: '#000' },
    leave:   { bg: theme.info, label: 'On Leave', color: '#fff' },
    absent:  { bg: theme.dangerBg || theme.danger + '20', label: 'Absent', color: theme.danger },
    weekend: { bg: theme.surface, label: 'Weekend', color: theme.textMuted },
    future:  { bg: 'transparent', label: 'Upcoming', color: theme.textMuted },
  }

  const selectedData = selected ? getDayData(selected) : null

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.accent, fontWeight: '700', marginBottom: '8px' }}>ATTENDANCE & LEAVE</div>
        <div style={{ fontSize: '32px', fontWeight: '900', letterSpacing: '-2px', color: theme.text }}>CALENDAR.</div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        {Object.entries(statusConfig).filter(([k]) => k !== 'future').map(([key, val]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: '10px', height: '10px', background: val.bg, border: `1px solid ${theme.border}` }} />
            <span style={{ fontSize: '9px', letterSpacing: '1px', color: theme.textMuted, fontWeight: '700' }}>{val.label.toUpperCase()}</span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '10px', height: '10px', background: theme.infoBg || theme.info + '30', border: `2px solid ${theme.info}` }} />
          <span style={{ fontSize: '9px', letterSpacing: '1px', color: theme.textMuted, fontWeight: '700' }}>TEAM ON LEAVE</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '24px' }}>
        {/* Calendar */}
        <div>
          {/* Month nav */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <button
              onClick={() => setCurrentMonth(m => subMonths(m, 1))}
              style={{ background: 'transparent', border: `2px solid ${theme.border}`, color: theme.text, padding: '8px 14px', cursor: 'pointer', fontSize: '12px', fontFamily: 'inherit', fontWeight: '700' }}
            >
              ←
            </button>
            <div style={{ fontSize: '14px', fontWeight: '900', letterSpacing: '2px', color: theme.text }}>
              {format(currentMonth, 'MMMM yyyy').toUpperCase()}
            </div>
            <button
              onClick={() => setCurrentMonth(m => addMonths(m, 1))}
              style={{ background: 'transparent', border: `2px solid ${theme.border}`, color: theme.text, padding: '8px 14px', cursor: 'pointer', fontSize: '12px', fontFamily: 'inherit', fontWeight: '700' }}
            >
              →
            </button>
          </div>

          {/* Day headers */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', marginBottom: '2px' }}>
            {['SUN','MON','TUE','WED','THU','FRI','SAT'].map(d => (
              <div key={d} style={{ textAlign: 'center', fontSize: '9px', letterSpacing: '1px', fontWeight: '700', color: theme.textMuted, padding: '8px 0' }}>{d}</div>
            ))}
          </div>

          {/* Days grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px' }}>
            {paddedDays.map((date, i) => {
              if (!date) return <div key={`pad-${i}`} />
              const status = getDayStatus(date)
              const cfg = statusConfig[status] || statusConfig.future
              const data = getDayData(date)
              const today = isToday(date)
              const isSelected = selected && format(selected, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd')
              const hasTeamLeave = data?.dayTeamLeaves?.length > 0

              return (
                <div
                  key={date.toISOString()}
                  onClick={() => setSelected(date)}
                  style={{
                    aspectRatio: '1',
                    background: cfg.bg,
                    border: isSelected
                      ? `2px solid ${theme.accent}`
                      : today
                        ? `2px solid ${theme.text}`
                        : hasTeamLeave
                          ? `2px solid ${theme.info}`
                          : `1px solid ${theme.border}`,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'opacity 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.opacity = '0.8'}
                  onMouseLeave={e => e.currentTarget.style.opacity = '1'}
                >
                  <span style={{ fontSize: '11px', fontWeight: today ? '900' : '700', color: cfg.color }}>
                    {format(date, 'd')}
                  </span>
                  {data?.daySessions?.length > 0 && (
                    <div style={{ width: '4px', height: '4px', background: cfg.color, borderRadius: '50%', marginTop: '2px', opacity: 0.7 }} />
                  )}
                  {hasTeamLeave && (
                    <div style={{ position: 'absolute', top: '2px', right: '2px', width: '4px', height: '4px', background: theme.info, borderRadius: '50%' }} />
                  )}
                </div>
              )
            })}
          </div>

          {/* Monthly summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0', marginTop: '24px', border: `2px solid ${theme.border}` }}>
            {[
              { label: 'PRESENT', value: days.filter(d => getDayStatus(d) === 'full').length, color: theme.success },
              { label: 'PARTIAL', value: days.filter(d => getDayStatus(d) === 'partial').length, color: theme.warning },
              { label: 'ON LEAVE', value: days.filter(d => getDayStatus(d) === 'leave').length, color: theme.info },
              { label: 'ABSENT', value: days.filter(d => getDayStatus(d) === 'absent').length, color: theme.danger },
            ].map((s, i) => (
              <div key={i} style={{ padding: '16px', borderRight: i < 3 ? `2px solid ${theme.border}` : 'none', background: theme.card, textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: '900', color: s.color }}>{s.value}</div>
                <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, marginTop: '4px' }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Day detail panel */}
        <div>
          <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.textMuted, fontWeight: '700', marginBottom: '16px' }}>
            {selected ? format(selected, 'EEEE, dd MMMM').toUpperCase() : 'SELECT A DAY'}
          </div>

          {selected && selectedData ? (
            <div>
              {/* Sessions */}
              <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '16px', marginBottom: '12px' }}>
                <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700', marginBottom: '12px' }}>MY SESSIONS</div>
                {selectedData.daySessions.length === 0 ? (
                  <div style={{ fontSize: '10px', color: theme.textMuted }}>No sessions this day</div>
                ) : selectedData.daySessions.map(s => (
                  <div key={s.id} style={{ marginBottom: '8px' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', color: theme.text }}>{s.total_work_minutes || 0} min worked</div>
                    <div style={{ fontSize: '10px', color: theme.textMuted }}>{s.total_break_minutes || 0} min break · {s.status}</div>
                  </div>
                ))}
              </div>

              {/* Own leave */}
              {selectedData.dayLeaves.length > 0 && (
                <div style={{ background: theme.card, border: `2px solid ${theme.info}`, padding: '16px', marginBottom: '12px' }}>
                  <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.info, fontWeight: '700', marginBottom: '8px' }}>ON LEAVE</div>
                  {selectedData.dayLeaves.map((l, i) => (
                    <div key={i} style={{ fontSize: '11px', color: theme.text }}>{l.leave_type} — {l.reason}</div>
                  ))}
                </div>
              )}

              {/* Team leaves */}
              {selectedData.dayTeamLeaves.length > 0 && (
                <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '16px' }}>
                  <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700', marginBottom: '12px' }}>
                    TEAM ON LEAVE ({selectedData.dayTeamLeaves.length})
                  </div>
                  {selectedData.dayTeamLeaves.map((l, i) => (
                    <div key={i} style={{ fontSize: '10px', color: theme.textSub, marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{l.employee_name || 'Team member'}</span>
                      <span style={{ color: theme.info }}>{l.leave_type}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '30px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: theme.border, marginBottom: '8px' }}>▦</div>
              <div style={{ fontSize: '10px', color: theme.textMuted, letterSpacing: '1px' }}>CLICK ANY DAY TO VIEW DETAILS</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
