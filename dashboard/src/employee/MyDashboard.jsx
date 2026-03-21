import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTheme } from './ThemeContext'
import { useAuthStore } from '../store/authStore'
import { sessionsAPI, flagsAPI, appealsAPI } from '../services/api'
import { calculateLeaveBalance, LEAVE_TYPES } from './leaveUtils'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { format, subDays } from 'date-fns'

function toUTC(iso) {
  if (!iso) return iso
  if (iso.includes('Z') || iso.includes('+')) return iso
  return iso + 'Z'
}

function Divider({ theme }) {
  return <div style={{ height: '2px', background: theme.border, margin: '20px 0' }} />
}

function LeaveBar({ type, balance, theme }) {
  const info = LEAVE_TYPES[type]
  const pct = balance.total > 0 ? Math.round((balance.balance / balance.total) * 100) : 0
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 10, letterSpacing: '1px', fontWeight: 700, color: theme.textSub }}>{info.name.toUpperCase()}</span>
        <span style={{ fontSize: 10, color: theme.textMuted }}>
          <span style={{ color: info.color, fontWeight: 900 }}>{balance.balance}</span> / {balance.total} days
        </span>
      </div>
      <div style={{ height: 6, background: theme.border }}>
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
  const [flags,    setFlags]    = useState([])
  const [appeals,  setAppeals]  = useState([])
  const [loading,  setLoading]  = useState(true)

  const hour     = new Date().getHours()
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

  const weekData = Array.from({ length: 7 }, (_, i) => {
    const d      = subDays(new Date(), 6 - i)
    const dayStr = format(d, 'yyyy-MM-dd')
    const total  = sessions
      .filter(s => format(new Date(toUTC(s.start_time)), 'yyyy-MM-dd') === dayStr)
      .reduce((a, s) => a + (s.total_work_minutes || 0), 0)
    return { day: format(d, 'EEE').toUpperCase(), minutes: total, target: 400 }
  })

  const totalWork       = sessions.reduce((a, s) => a + (s.total_work_minutes || 0), 0)
  const completedSessions = sessions.filter(s => s.status === 'completed').length
  const pendingFlags    = flags.filter(f => !f.reviewed).length
  const weekWork        = weekData.reduce((a, d) => a + d.minutes, 0)
  const weekHours       = Math.floor(weekWork / 60)
  const weekMins        = weekWork % 60

  let streak = 0
  for (let i = 0; i < 30; i++) {
    const d = subDays(new Date(), i)
    const dayStr = format(d, 'yyyy-MM-dd')
    const has = sessions.some(s =>
      format(new Date(toUTC(s.start_time)), 'yyyy-MM-dd') === dayStr && (s.total_work_minutes || 0) > 60
    )
    if (has) streak++
    else if (i > 0) break
  }

  const leaveBalance = calculateLeaveBalance(
    user?.created_at || new Date().toISOString(), [], completedSessions * 8
  )

  const t = theme

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

  if (loading) return (
    <div style={{ color: t.textMuted, fontSize: 11, letterSpacing: '2px', padding: '40px 0' }}>LOADING...</div>
  )

  return (
    <div>
      {/* ── Responsive styles ── */}
      <style>{`
        .dash-grid-4 { display: grid; grid-template-columns: repeat(2, 1fr); }
        .dash-grid-2 { display: grid; grid-template-columns: 1fr; gap: 20px; }
        @media (min-width: 640px) {
          .dash-grid-4 { grid-template-columns: repeat(4, 1fr); }
          .dash-grid-2 { grid-template-columns: 1fr 1fr; }
        }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 9, letterSpacing: '3px', color: t.accent, fontWeight: 700, marginBottom: 6 }}>{greeting}</div>
        <div style={{ fontSize: 'clamp(24px, 6vw, 36px)', fontWeight: 900, letterSpacing: '-2px', color: t.text, lineHeight: 1 }}>
          {user?.full_name?.split(' ')[0]?.toUpperCase()}.
        </div>
        <div style={{ fontSize: 11, color: t.textMuted, letterSpacing: '1px', marginTop: 8 }}>
          {format(new Date(), 'EEEE, dd MMMM yyyy').toUpperCase()} — {user?.department?.toUpperCase()}
        </div>
      </div>

      {/* Stat grid */}
      <div className="dash-grid-4" style={{ marginBottom: 20, border: `2px solid ${t.border}` }}>
        {[
          { label: 'THIS WEEK',  value: `${weekHours}H ${weekMins}M`, sub: 'of 40h target',       accent: t.accent },
          { label: 'SESSIONS',   value: completedSessions,             sub: `${sessions.length} total`, accent: t.text },
          { label: 'STREAK',     value: `${streak}D`,                  sub: 'consecutive',          accent: streak >= 5 ? t.success : t.text },
          { label: 'OPEN FLAGS', value: pendingFlags,                  sub: pendingFlags > 0 ? 'needs attention' : 'all clear', accent: pendingFlags > 0 ? t.danger : t.success },
        ].map((stat, i) => (
          <div key={i} style={{
            padding: '16px 14px',
            background: t.card,
            borderRight: i < 3 ? `2px solid ${t.border}` : 'none',
            borderBottom: 0,
          }}>
            <div style={{ fontSize: 8, letterSpacing: '2px', color: t.textMuted, fontWeight: 700, marginBottom: 6 }}>{stat.label}</div>
            <div style={{ fontSize: 'clamp(20px, 5vw, 30px)', fontWeight: 900, letterSpacing: '-1px', color: stat.accent, lineHeight: 1 }}>{stat.value}</div>
            <div style={{ fontSize: 9, color: t.textMuted, marginTop: 4 }}>{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="dash-grid-2">
        {/* Work chart */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 9, letterSpacing: '3px', color: t.textMuted, fontWeight: 700 }}>WEEKLY WORK HOURS</span>
            <span onClick={() => navigate('/my/sessions')} style={{ fontSize: 9, letterSpacing: '2px', color: t.accent, cursor: 'pointer', fontWeight: 700 }}>ALL →</span>
          </div>
          <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: '16px 12px' }}>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={weekData} barSize={18}>
                <XAxis dataKey="day" tick={{ fill: t.textMuted, fontSize: 9, letterSpacing: 1, fontFamily: 'monospace' }} axisLine={false} tickLine={false} />
                <YAxis hide />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="minutes" fill={t.accent} radius={0} />
                <Bar dataKey="target"  fill={t.border}  radius={0} />
              </BarChart>
            </ResponsiveContainer>
            <div style={{ display: 'flex', gap: 14, marginTop: 8 }}>
              {[{ c: t.accent, l: 'WORKED' }, { c: t.border, l: 'TARGET' }].map(({ c, l }) => (
                <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <div style={{ width: 10, height: 10, background: c }} />
                  <span style={{ fontSize: 8, color: t.textMuted, letterSpacing: '1px' }}>{l}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Leave balances */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 9, letterSpacing: '3px', color: t.textMuted, fontWeight: 700 }}>LEAVE BALANCES</span>
            <span onClick={() => navigate('/my/leave')} style={{ fontSize: 9, letterSpacing: '2px', color: t.accent, cursor: 'pointer', fontWeight: 700 }}>APPLY →</span>
          </div>
          <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: '16px' }}>
            {Object.entries(leaveBalance).map(([type, balance]) => (
              <LeaveBar key={type} type={type} balance={balance} theme={t} />
            ))}
          </div>
        </div>
      </div>

      <Divider theme={t} />

      {/* Sessions + Flags */}
      <div className="dash-grid-2">
        {/* Recent sessions */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 9, letterSpacing: '3px', color: t.textMuted, fontWeight: 700 }}>RECENT SESSIONS</span>
            <span onClick={() => navigate('/my/sessions')} style={{ fontSize: 9, letterSpacing: '2px', color: t.accent, cursor: 'pointer', fontWeight: 700 }}>VIEW ALL →</span>
          </div>
          <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: '0 16px' }}>
            {sessions.slice(0, 5).map((s, i) => {
              const sc = s.status === 'completed' ? t.success : s.status === 'active' ? t.info : t.warning
              return (
                <div key={s.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px 0', borderBottom: `1px solid ${t.border}`,
                }}>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 700, color: t.text }}>
                      {format(new Date(toUTC(s.start_time)), 'dd MMM yyyy')}
                    </div>
                    <div style={{ fontSize: 10, color: t.textMuted, marginTop: 2 }}>
                      {s.total_work_minutes || 0}m · {s.total_break_minutes || 0}m break
                    </div>
                  </div>
                  <div style={{ fontSize: 9, fontWeight: 700, color: sc, background: sc + '20', padding: '3px 8px' }}>
                    {s.status?.toUpperCase()}
                  </div>
                </div>
              )
            })}
            {sessions.length === 0 && (
              <div style={{ padding: '28px 0', textAlign: 'center', fontSize: 10, color: t.textMuted, letterSpacing: '1px' }}>
                NO SESSIONS YET
              </div>
            )}
          </div>
        </div>

        {/* Flags */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 9, letterSpacing: '3px', color: t.textMuted, fontWeight: 700 }}>MY FLAGS</span>
            <span onClick={() => navigate('/my/flags')} style={{ fontSize: 9, letterSpacing: '2px', color: t.accent, cursor: 'pointer', fontWeight: 700 }}>VIEW ALL →</span>
          </div>
          <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: '0 16px' }}>
            {flags.slice(0, 4).map(f => {
              const types = Object.keys(f.detections || {})
              const readable = {
                mechanical_typing: 'Consistent typing pattern',
                long_idle: 'Extended idle period',
                rapid_paste: 'Multiple paste events',
                mouse_jiggler: 'Mouse movement pattern',
                clock_in_clock_out: 'Minimal activity',
                burst_then_idle: 'Activity burst then idle',
              }
              return (
                <div key={f.id} style={{ padding: '12px 0', borderBottom: `1px solid ${t.border}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: t.text, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {readable[types[0]] || types[0]?.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: 9, color: t.textMuted, marginTop: 2 }}>
                        {Math.round((f.confidence_score || 0) * 100)}% · {f.overall_severity}
                      </div>
                    </div>
                    {!f.reviewed && (
                      <button
                        onClick={() => navigate('/my/flags')}
                        style={{ fontSize: 8, letterSpacing: '1px', fontWeight: 700, padding: '3px 8px', flexShrink: 0, background: 'transparent', border: `2px solid ${t.accent}`, color: t.accent, cursor: 'pointer', fontFamily: 'inherit' }}
                      >
                        APPEAL
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
            {flags.length === 0 && (
              <div style={{ padding: '28px 0', textAlign: 'center', fontSize: 10, color: t.success, letterSpacing: '1px' }}>
                ✓ ALL CLEAR
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}