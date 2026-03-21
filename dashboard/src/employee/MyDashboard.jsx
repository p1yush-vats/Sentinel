import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from './ThemeContext'
import { useAuthStore } from '../store/authStore'
import { sessionsAPI, flagsAPI, appealsAPI } from '../services/api'
import { calculateLeaveBalance, LEAVE_TYPES } from './leaveUtils'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { format, subDays, startOfWeek } from 'date-fns'

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+')) return iso
  return iso + 'Z'
}

function Divider({ theme }) {
  return <div style={{ height: '2px', background: theme.border, margin: '24px 0' }} />
}

function StatBox({ label, value, sub, accent, theme }) {
  return (
    <div style={{
      background: theme.card,
      border: `2px solid ${theme.border}`,
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
    }}>
      <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700' }}>{label}</div>
      <div style={{ fontSize: '28px', fontWeight: '900', letterSpacing: '-2px', color: accent || theme.text, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: '10px', color: theme.textMuted }}>{sub}</div>}
    </div>
  )
}

function LeaveBar({ type, balance, theme }) {
  const info = LEAVE_TYPES[type]
  const pct = balance.total > 0 ? Math.round((balance.balance / balance.total) * 100) : 0
  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ fontSize: '10px', letterSpacing: '1px', fontWeight: '700', color: theme.textSub }}>{info.name.toUpperCase()}</span>
        <span style={{ fontSize: '10px', color: theme.textMuted }}>
          <span style={{ color: info.color, fontWeight: '900' }}>{balance.balance}</span> / {balance.total} days
        </span>
      </div>
      <div style={{ height: '6px', background: theme.border }}>
        <div style={{ height: '100%', width: `${pct}%`, background: info.color, transition: 'width 0.8s ease' }} />
      </div>
    </div>
  )
}

export default function MyDashboard() {
  const { theme } = useTheme()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [sessions, setSessions] = useState([])
  const [flags, setFlags] = useState([])
  const [appeals, setAppeals] = useState([])
  const [loading, setLoading] = useState(true)

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'GOOD MORNING' : hour < 17 ? 'GOOD AFTERNOON' : 'GOOD EVENING'

  useEffect(() => {
    Promise.all([
      sessionsAPI.getMySessions({ limit: 100 }),
      flagsAPI.getMyFlags({ limit: 50 }),
      appealsAPI.getMyAppeals({ limit: 50 }),
    ]).then(([sRes, fRes, aRes]) => {
      setSessions(sRes.data?.sessions || [])
      setFlags(fRes.data?.abnormalities || [])
      setAppeals(aRes.data?.appeals || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  // Week chart data
  const weekData = Array.from({ length: 7 }, (_, i) => {
    const d = subDays(new Date(), 6 - i)
    const dayStr = format(d, 'yyyy-MM-dd')
    const daySessions = sessions.filter(s => {
      const st = new Date(toUTC(s.start_time))
      return format(st, 'yyyy-MM-dd') === dayStr
    })
    const totalWork = daySessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
    return { day: format(d, 'EEE').toUpperCase(), minutes: totalWork, target: 400 }
  })

  // Stats
  const totalWork = sessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
  const completedSessions = sessions.filter(s => s.status === 'completed').length
  const pendingFlags = flags.filter(f => !f.reviewed).length
  const weekWork = weekData.reduce((a, d) => a + d.minutes, 0)
  const weekHours = Math.floor(weekWork / 60)
  const weekMins = weekWork % 60

  // Streak
  let streak = 0
  for (let i = 0; i < 30; i++) {
    const d = subDays(new Date(), i)
    const dayStr = format(d, 'yyyy-MM-dd')
    const hasSession = sessions.some(s => {
      const st = new Date(toUTC(s.start_time))
      return format(st, 'yyyy-MM-dd') === dayStr && (s.total_work_minutes || 0) > 60
    })
    if (hasSession) streak++
    else if (i > 0) break
  }

  const leaveBalance = calculateLeaveBalance(
    user?.created_at || new Date().toISOString(),
    [],
    completedSessions * 8
  )

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '10px 14px' }}>
        <div style={{ fontSize: '10px', color: theme.textMuted, letterSpacing: '1px', marginBottom: '4px' }}>{label}</div>
        <div style={{ fontSize: '14px', fontWeight: '900', color: theme.accent }}>{Math.floor(payload[0].value / 60)}h {payload[0].value % 60}m</div>
        <div style={{ fontSize: '10px', color: theme.textMuted }}>TARGET: 6h 40m</div>
      </div>
    )
  }

  const s = {
    heading: { fontSize: '11px', letterSpacing: '3px', color: theme.textMuted, fontWeight: '700', marginBottom: '16px' },
    sectionTitle: { fontSize: '11px', letterSpacing: '3px', color: theme.textMuted, fontWeight: '700', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
    link: { fontSize: '9px', letterSpacing: '2px', color: theme.accent, cursor: 'pointer', fontWeight: '700' },
    grid3: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0', border: `2px solid ${theme.border}` },
    grid4: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' },
    grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' },
    flagCard: {
      background: theme.card,
      border: `2px solid ${theme.border}`,
      borderLeft: `4px solid ${theme.danger}`,
      padding: '14px 16px',
      marginBottom: '8px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    sessionRow: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '12px 0',
      borderBottom: `1px solid ${theme.border}`,
    },
  }

  if (loading) return (
    <div style={{ color: theme.textMuted, fontSize: '11px', letterSpacing: '2px', padding: '40px 0' }}>
      LOADING...
    </div>
  )

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.accent, fontWeight: '700', marginBottom: '8px' }}>{greeting}</div>
        <div style={{ fontSize: '36px', fontWeight: '900', letterSpacing: '-2px', color: theme.text, lineHeight: 1 }}>
          {user?.full_name?.split(' ')[0]?.toUpperCase()}.
        </div>
        <div style={{ fontSize: '11px', color: theme.textMuted, letterSpacing: '1px', marginTop: '8px' }}>
          {format(new Date(), 'EEEE, dd MMMM yyyy').toUpperCase()} — {user?.department?.toUpperCase()}
        </div>
      </div>

      {/* Stat grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0', marginBottom: '24px', border: `2px solid ${theme.border}` }}>
        {[
          { label: 'THIS WEEK', value: `${weekHours}H ${weekMins}M`, sub: 'of 40h target', accent: theme.accent },
          { label: 'SESSIONS', value: completedSessions, sub: `${sessions.length} total`, accent: theme.text },
          { label: 'STREAK', value: `${streak}D`, sub: 'consecutive days', accent: streak >= 5 ? theme.success : theme.text },
          { label: 'OPEN FLAGS', value: pendingFlags, sub: pendingFlags > 0 ? 'needs attention' : 'all clear', accent: pendingFlags > 0 ? theme.danger : theme.success },
        ].map((stat, i) => (
          <div key={i} style={{
            ...( i < 3 ? { borderRight: `2px solid ${theme.border}` } : {} ),
            padding: '20px',
            background: theme.card,
          }}>
            <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700', marginBottom: '8px' }}>{stat.label}</div>
            <div style={{ fontSize: '32px', fontWeight: '900', letterSpacing: '-2px', color: stat.accent, lineHeight: 1 }}>{stat.value}</div>
            <div style={{ fontSize: '10px', color: theme.textMuted, marginTop: '4px' }}>{stat.sub}</div>
          </div>
        ))}
      </div>

      <div style={s.grid2}>
        {/* Work chart */}
        <div>
          <div style={s.sectionTitle}>
            <span>WEEKLY WORK HOURS</span>
            <span style={s.link} onClick={() => navigate('/my/sessions')}>ALL SESSIONS →</span>
          </div>
          <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '20px' }}>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={weekData} barSize={20}>
                <XAxis dataKey="day" tick={{ fill: theme.textMuted, fontSize: 9, letterSpacing: 1, fontFamily: 'monospace' }} axisLine={false} tickLine={false} />
                <YAxis hide />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="minutes" fill={theme.accent} radius={0} />
                <Bar dataKey="target" fill={theme.border} radius={0} />
              </BarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '10px', height: '10px', background: theme.accent }} />
                <span style={{ fontSize: '9px', color: theme.textMuted, letterSpacing: '1px' }}>WORKED</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '10px', height: '10px', background: theme.border }} />
                <span style={{ fontSize: '9px', color: theme.textMuted, letterSpacing: '1px' }}>TARGET</span>
              </div>
            </div>
          </div>
        </div>

        {/* Leave balances */}
        <div>
          <div style={s.sectionTitle}>
            <span>LEAVE BALANCES</span>
            <span style={s.link} onClick={() => navigate('/my/leave')}>APPLY →</span>
          </div>
          <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '20px' }}>
            {Object.entries(leaveBalance).map(([type, balance]) => (
              <LeaveBar key={type} type={type} balance={balance} theme={theme} />
            ))}
          </div>
        </div>
      </div>

      <Divider theme={theme} />

      <div style={s.grid2}>
        {/* Recent sessions */}
        <div>
          <div style={s.sectionTitle}>
            <span>RECENT SESSIONS</span>
            <span style={s.link} onClick={() => navigate('/my/sessions')}>VIEW ALL →</span>
          </div>
          <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '0 20px' }}>
            {sessions.slice(0, 5).map(s => {
              const statusColor = s.status === 'completed' ? theme.success : s.status === 'active' ? theme.info : theme.warning
              return (
                <div key={s.id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '14px 0',
                  borderBottom: `1px solid ${theme.border}`,
                }}>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: '700', color: theme.text, letterSpacing: '-0.3px' }}>
                      {format(new Date(toUTC(s.start_time)), 'dd MMM yyyy')}
                    </div>
                    <div style={{ fontSize: '10px', color: theme.textMuted, marginTop: '2px' }}>
                      {s.total_work_minutes || 0}m worked · {s.total_break_minutes || 0}m break
                    </div>
                  </div>
                  <div style={{ fontSize: '9px', letterSpacing: '1px', fontWeight: '700', color: statusColor, background: statusColor + '20', padding: '4px 10px' }}>
                    {s.status?.toUpperCase()}
                  </div>
                </div>
              )
            })}
            {sessions.length === 0 && (
              <div style={{ padding: '30px 0', textAlign: 'center', fontSize: '10px', color: theme.textMuted, letterSpacing: '1px' }}>
                NO SESSIONS YET
              </div>
            )}
          </div>
        </div>

        {/* Flags */}
        <div>
          <div style={s.sectionTitle}>
            <span>MY FLAGS</span>
            <span style={s.link} onClick={() => navigate('/my/flags')}>VIEW ALL →</span>
          </div>
          <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '0 20px' }}>
            {flags.slice(0, 4).map(f => {
              const types = Object.keys(f.detections || {})
              const readable = {
                mechanical_typing: 'Consistent typing pattern',
                long_idle: 'Extended idle period',
                rapid_paste: 'Multiple paste events',
                suspicious_paste: 'Large paste detected',
                mouse_jiggler: 'Mouse movement pattern',
                clock_in_clock_out: 'Minimal activity after login',
                burst_then_idle: 'Activity burst then idle',
              }
              return (
                <div key={f.id} style={{
                  padding: '14px 0',
                  borderBottom: `1px solid ${theme.border}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontSize: '11px', fontWeight: '700', color: theme.text }}>
                        {readable[types[0]] || types[0]?.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: '10px', color: theme.textMuted, marginTop: '2px' }}>
                        {Math.round((f.confidence_score || 0) * 100)}% confidence · {f.overall_severity}
                      </div>
                    </div>
                    {!f.reviewed && (
                      <button
                        onClick={() => navigate('/my/appeals')}
                        style={{ fontSize: '9px', letterSpacing: '1px', fontWeight: '700', padding: '4px 10px', background: 'transparent', border: `2px solid ${theme.accent}`, color: theme.accent, cursor: 'pointer' }}
                      >
                        APPEAL
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
            {flags.length === 0 && (
              <div style={{ padding: '30px 0', textAlign: 'center', fontSize: '10px', color: theme.success, letterSpacing: '1px' }}>
                ✓ ALL CLEAR — NO FLAGS
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
