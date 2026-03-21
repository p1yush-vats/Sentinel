import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { useAuthStore } from '../store/authStore'
import { LEAVE_TYPES, calculateLeaveBalance, workingDaysBetween } from './leaveUtils'
import api from '../services/api'
import toast from 'react-hot-toast'
import { format, addDays } from 'date-fns'

function LeaveTypeCard({ type, balance, selected, onClick, theme }) {
  const info = LEAVE_TYPES[type]
  const pct = balance.total > 0 ? Math.round((balance.balance / balance.total) * 100) : 0
  return (
    <div
      onClick={() => onClick(type)}
      style={{
        background: theme.card,
        border: `2px solid ${selected ? info.color : theme.border}`,
        padding: '16px',
        cursor: 'pointer',
        transition: 'border-color 0.2s',
        position: 'relative',
      }}
    >
      {selected && (
        <div style={{ position: 'absolute', top: '10px', right: '10px', width: '8px', height: '8px', background: info.color }} />
      )}
      <div style={{ fontSize: '9px', letterSpacing: '2px', fontWeight: '700', color: info.color, marginBottom: '8px' }}>{info.code}</div>
      <div style={{ fontSize: '12px', fontWeight: '700', color: theme.text, marginBottom: '4px' }}>{info.name}</div>
      <div style={{ fontSize: '22px', fontWeight: '900', letterSpacing: '-1px', color: selected ? info.color : theme.text }}>
        {balance.balance}<span style={{ fontSize: '12px', fontWeight: '400', color: theme.textMuted }}>/{balance.total}</span>
      </div>
      <div style={{ fontSize: '9px', color: theme.textMuted, marginTop: '4px', marginBottom: '10px' }}>DAYS REMAINING</div>
      <div style={{ height: '3px', background: theme.border }}>
        <div style={{ height: '100%', width: `${pct}%`, background: info.color }} />
      </div>
      <div style={{ fontSize: '9px', color: theme.textMuted, marginTop: '8px', lineHeight: 1.6 }}>{info.description}</div>
    </div>
  )
}

const STATUS_COLORS = {
  approved: '#00c851',
  rejected: '#ff4444',
  pending: '#ffbb00',
}

export default function MyLeave() {
  const { theme } = useTheme()
  const { user } = useAuthStore()
  const [leaves, setLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedType, setSelectedType] = useState('CL')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [tab, setTab] = useState('apply') // apply | history

  const leaveBalance = calculateLeaveBalance(
    user?.created_at || new Date().toISOString(),
    leaves.filter(l => l.status === 'approved').map(l => ({
      type: l.leave_type,
      days: l.days_requested || 1,
    })),
    50
  )

  useEffect(() => {
    api.get('/leaves/').then(r => setLeaves(r.data?.leaves || [])).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const workingDays = fromDate && toDate
    ? workingDaysBetween(new Date(fromDate), new Date(toDate))
    : 0

  const handleApply = async () => {
    if (!fromDate || !toDate || !reason.trim()) {
      toast.error('Fill all fields')
      return
    }
    if (workingDays <= 0) {
      toast.error('Invalid date range')
      return
    }
    const bal = leaveBalance[selectedType]
    if (bal && workingDays > bal.balance) {
      toast.error(`Insufficient ${selectedType} balance. You have ${bal.balance} days.`)
      return
    }

    setSubmitting(true)
    try {
      await api.post('/leaves/', {
        leave_type: selectedType,
        from_date: fromDate,
        to_date: toDate,
        days_requested: workingDays,
        reason,
      })
      toast.success('Leave application submitted')
      setFromDate('')
      setToDate('')
      setReason('')
      const r = await api.get('/leaves/')
      setLeaves(r.data?.leaves || [])
      setTab('history')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to submit')
    } finally {
      setSubmitting(false)
    }
  }

  const inp = {
    width: '100%',
    background: theme.surface,
    border: `2px solid ${theme.border}`,
    color: theme.text,
    padding: '10px 14px',
    fontSize: '12px',
    fontFamily: 'inherit',
    outline: 'none',
    boxSizing: 'border-box',
  }

  const label = {
    fontSize: '9px',
    letterSpacing: '2px',
    fontWeight: '700',
    color: theme.textMuted,
    marginBottom: '6px',
    display: 'block',
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.accent, fontWeight: '700', marginBottom: '8px' }}>LEAVE MANAGEMENT</div>
        <div style={{ fontSize: '32px', fontWeight: '900', letterSpacing: '-2px', color: theme.text }}>MY LEAVE.</div>
      </div>

      {/* Leave type cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0', marginBottom: '32px', border: `2px solid ${theme.border}` }}>
        {Object.keys(LEAVE_TYPES).map((type, i) => (
          <div key={type} style={{ borderRight: i < 3 ? `2px solid ${theme.border}` : 'none' }}>
            <LeaveTypeCard
              type={type}
              balance={leaveBalance[type] || { balance: 0, total: 0 }}
              selected={selectedType === type}
              onClick={setSelectedType}
              theme={theme}
            />
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: `2px solid ${theme.border}`, marginBottom: '24px' }}>
        {['apply', 'history'].map(t => (
          <div
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: '12px 24px',
              fontSize: '10px',
              letterSpacing: '2px',
              fontWeight: '700',
              cursor: 'pointer',
              color: tab === t ? theme.text : theme.textMuted,
              borderBottom: tab === t ? `2px solid ${theme.accent}` : '2px solid transparent',
              marginBottom: '-2px',
            }}
          >
            {t === 'apply' ? 'APPLY FOR LEAVE' : 'MY HISTORY'}
          </div>
        ))}
      </div>

      {tab === 'apply' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
          {/* Apply form */}
          <div>
            <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '24px' }}>
              {/* Type info */}
              <div style={{ background: theme.surface, border: `2px solid ${LEAVE_TYPES[selectedType].color}`, padding: '14px', marginBottom: '20px' }}>
                <div style={{ fontSize: '9px', letterSpacing: '2px', fontWeight: '700', color: LEAVE_TYPES[selectedType].color, marginBottom: '6px' }}>
                  {LEAVE_TYPES[selectedType].code} — {LEAVE_TYPES[selectedType].fullName.toUpperCase()}
                </div>
                <div style={{ fontSize: '11px', color: theme.textSub, lineHeight: 1.6 }}>
                  {LEAVE_TYPES[selectedType].description}
                </div>
                {LEAVE_TYPES[selectedType].requiresCertificate && (
                  <div style={{ fontSize: '10px', color: theme.warning, marginTop: '8px', fontWeight: '700' }}>
                    ⚠ MEDICAL CERTIFICATE MAY BE REQUIRED
                  </div>
                )}
                {LEAVE_TYPES[selectedType].minNoticeDays > 0 && (
                  <div style={{ fontSize: '10px', color: theme.info, marginTop: '4px' }}>
                    ℹ MIN {LEAVE_TYPES[selectedType].minNoticeDays} DAYS NOTICE REQUIRED
                  </div>
                )}
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={label}>LEAVE TYPE</label>
                <select value={selectedType} onChange={e => setSelectedType(e.target.value)} style={inp}>
                  {Object.entries(LEAVE_TYPES).map(([k, v]) => (
                    <option key={k} value={k}>{v.code} — {v.name} ({leaveBalance[k]?.balance || 0} days left)</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div>
                  <label style={label}>FROM DATE</label>
                  <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)}
                    min={format(new Date(), 'yyyy-MM-dd')} style={inp} />
                </div>
                <div>
                  <label style={label}>TO DATE</label>
                  <input type="date" value={toDate} onChange={e => setToDate(e.target.value)}
                    min={fromDate || format(new Date(), 'yyyy-MM-dd')} style={inp} />
                </div>
              </div>

              {workingDays > 0 && (
                <div style={{ background: theme.surface, border: `2px solid ${theme.border}`, padding: '12px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '10px', color: theme.textMuted, letterSpacing: '1px' }}>WORKING DAYS</span>
                  <span style={{ fontSize: '14px', fontWeight: '900', color: theme.accent }}>{workingDays}</span>
                </div>
              )}

              <div style={{ marginBottom: '20px' }}>
                <label style={label}>REASON</label>
                <textarea
                  value={reason}
                  onChange={e => setReason(e.target.value)}
                  rows={4}
                  placeholder="Briefly describe your reason for leave..."
                  style={{ ...inp, resize: 'vertical', lineHeight: 1.6 }}
                />
              </div>

              <button
                onClick={handleApply}
                disabled={submitting || !fromDate || !toDate || !reason}
                style={{
                  width: '100%',
                  padding: '14px',
                  background: submitting ? theme.border : theme.accent,
                  border: 'none',
                  color: '#fff',
                  fontSize: '10px',
                  letterSpacing: '3px',
                  fontWeight: '900',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                {submitting ? 'SUBMITTING...' : 'SUBMIT APPLICATION'}
              </button>
            </div>
          </div>

          {/* Rules summary */}
          <div>
            <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.textMuted, fontWeight: '700', marginBottom: '16px' }}>LEAVE POLICY SUMMARY</div>
            {Object.entries(LEAVE_TYPES).map(([type, info]) => (
              <div key={type} style={{ background: theme.card, border: `2px solid ${theme.border}`, borderLeft: `4px solid ${info.color}`, padding: '14px 16px', marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '700', color: theme.text }}>{info.fullName}</span>
                  <span style={{ fontSize: '11px', fontWeight: '900', color: info.color }}>{info.totalPerYear}d/yr</span>
                </div>
                <div style={{ fontSize: '10px', color: theme.textMuted, lineHeight: 1.6 }}>
                  {info.accrualRate} · Carry forward: {info.carryForward > 0 ? `${info.carryForward} days` : 'None'} ·
                  Encashable: {info.encashable ? 'Yes' : 'No'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'history' && (
        <div>
          {loading ? (
            <div style={{ color: theme.textMuted, fontSize: '11px', letterSpacing: '2px' }}>LOADING...</div>
          ) : leaves.length === 0 ? (
            <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '40px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: theme.textMuted, letterSpacing: '2px' }}>NO LEAVE APPLICATIONS YET</div>
            </div>
          ) : (
            <div style={{ background: theme.card, border: `2px solid ${theme.border}` }}>
              {leaves.map((leave, i) => {
                const info = LEAVE_TYPES[leave.leave_type]
                const statusColor = STATUS_COLORS[leave.status] || theme.textMuted
                return (
                  <div key={leave.id} style={{
                    padding: '16px 20px',
                    borderBottom: i < leaves.length - 1 ? `1px solid ${theme.border}` : 'none',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}>
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                      <div style={{ width: '4px', alignSelf: 'stretch', background: info?.color || theme.border }} />
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: '700', color: theme.text }}>
                          {info?.name || leave.leave_type} — {leave.days_requested || 1} day{(leave.days_requested || 1) > 1 ? 's' : ''}
                        </div>
                        <div style={{ fontSize: '10px', color: theme.textMuted, marginTop: '2px' }}>
                          {leave.from_date} → {leave.to_date}
                        </div>
                        <div style={{ fontSize: '10px', color: theme.textSub, marginTop: '2px', fontStyle: 'italic' }}>
                          {leave.reason}
                        </div>
                        {leave.admin_response && (
                          <div style={{ fontSize: '10px', color: statusColor, marginTop: '4px' }}>
                            Admin: {leave.admin_response}
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ fontSize: '9px', letterSpacing: '1px', fontWeight: '700', color: statusColor, background: statusColor + '20', padding: '6px 12px' }}>
                      {leave.status?.toUpperCase()}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
