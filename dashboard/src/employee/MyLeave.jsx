import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { useAuthStore } from '../store/authStore'
import { LEAVE_TYPES, calculateLeaveBalance, workingDaysBetween } from './leaveUtils'
import api from '../services/api'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

const STATUS_COLORS = { approved: '#00c851', rejected: '#ff4444', pending: '#ffbb00', needs_info: '#33b5e5' }

function LeaveTypeCard({ type, balance, selected, onClick, theme }) {
  const info = LEAVE_TYPES[type]
  const pct  = balance.total > 0 ? Math.round((balance.balance / balance.total) * 100) : 0
  const t    = theme
  return (
    <div
      onClick={() => onClick(type)}
      style={{
        background: t.card, border: `2px solid ${selected ? info.color : t.border}`,
        padding: 14, cursor: 'pointer', transition: 'border-color 0.2s', position: 'relative',
      }}
    >
      {selected && <div style={{ position: 'absolute', top: 8, right: 8, width: 7, height: 7, background: info.color }} />}
      <div style={{ fontSize: 8, letterSpacing: '2px', fontWeight: 700, color: info.color, marginBottom: 6 }}>{info.code}</div>
      <div style={{ fontSize: 11, fontWeight: 700, color: t.text, marginBottom: 3 }}>{info.name}</div>
      <div style={{ fontSize: 'clamp(18px, 4vw, 22px)', fontWeight: 900, letterSpacing: '-1px', color: selected ? info.color : t.text }}>
        {balance.balance}<span style={{ fontSize: 11, fontWeight: 400, color: t.textMuted }}>/{balance.total}</span>
      </div>
      <div style={{ fontSize: 8, color: t.textMuted, marginTop: 2, marginBottom: 8 }}>DAYS LEFT</div>
      <div style={{ height: 3, background: t.border }}>
        <div style={{ height: '100%', width: `${pct}%`, background: info.color }} />
      </div>
    </div>
  )
}

export default function MyLeave() {
  const { theme } = useTheme()
  const { user }  = useAuthStore()
  const [leaves,       setLeaves]       = useState([])
  const [loading,      setLoading]      = useState(true)
  const [selectedType, setSelectedType] = useState('CL')
  const [fromDate,     setFromDate]     = useState('')
  const [toDate,       setToDate]       = useState('')
  const [reason,       setReason]       = useState('')
  const [submitting,   setSubmitting]   = useState(false)
  const [tab,          setTab]          = useState('apply')
  const [replyText,    setReplyText]    = useState({})
  const [replying,     setReplying]     = useState(null)
  const [medicalCert,  setMedicalCert]  = useState(null)
  const [certFileName, setCertFileName] = useState('')
  const t = theme

  const leaveBalance = calculateLeaveBalance(
    user?.created_at || new Date().toISOString(),
    leaves.filter(l => l.status === 'approved').map(l => ({ type: l.leave_type, days: l.days_requested || 1 })),
    50
  )

  const fetchLeaves = (silent = false) => {
    if (!silent) setLoading(true)
    api.get('/leaves/')
      .then(r => setLeaves(r.data?.leaves || []))
      .catch(() => {})
      .finally(() => {
        if (!silent) setLoading(false)
      })
  }

  useEffect(() => {
    fetchLeaves()
    const interval = setInterval(() => fetchLeaves(true), 15000)
    return () => clearInterval(interval)
  }, [])

  const workingDays = fromDate && toDate ? workingDaysBetween(new Date(fromDate), new Date(toDate)) : 0
  const needsCert = selectedType === 'ML' || (selectedType === 'SL' && workingDays >= 3)

  const handleApply = async () => {
    if (!fromDate || !toDate || !reason.trim()) { toast.error('Fill all fields'); return }
    if (workingDays <= 0) { toast.error('Invalid date range'); return }
    const bal = leaveBalance[selectedType]
    if (bal && workingDays > bal.balance) { toast.error(`Insufficient ${selectedType} balance (${bal.balance} days left)`); return }

    // Evidence validation
    if (needsCert && !medicalCert) {
      toast.error(`Medical certificate is mandatory for ${selectedType === 'ML' ? 'Maternity Leave' : 'Sick Leave (3+ days)'}`)
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
        medical_certificate: medicalCert
      })
      toast.success('Leave application submitted')
      setFromDate(''); setToDate(''); setReason(''); setMedicalCert(null); setCertFileName('')
      const r = await api.get('/leaves/')
      setLeaves(r.data?.leaves || [])
      setTab('history')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to submit')
    } finally { setSubmitting(false) }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (file.size > 2 * 1024 * 1024) {
      toast.error('File size must be under 2MB')
      return
    }

    setCertFileName(file.name)
    const reader = new FileReader()
    reader.onloadend = () => {
      setMedicalCert(reader.result)
    }
    reader.readAsDataURL(file)
  }

  const handleReply = async (id) => {
    const text = (replyText[id] || '').trim()
    if (!text) return toast.error('Enter a response')
    setReplying(id)
    try {
      await api.post(`/leaves/${id}/comment`, { message: text })
      toast.success('Reply sent')
      setReplyText(prev => ({ ...prev, [id]: '' }))
      const r = await api.get('/leaves/')
      setLeaves(r.data?.leaves || [])
    } catch (e) {
      toast.error('Failed to send reply')
    } finally {
      setReplying(null)
    }
  }

  const inp = {
    width: '100%', background: t.surface, border: `2px solid ${t.border}`,
    color: t.text, padding: '9px 12px', fontSize: 12, fontFamily: 'inherit',
    outline: 'none', boxSizing: 'border-box',
  }
  const lbl = { fontSize: 8, letterSpacing: '2px', fontWeight: 700, color: t.textMuted, marginBottom: 5, display: 'block' }

  return (
    <div>
      <style>{`
        .leave-type-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0; border: 2px solid ${t.border}; margin-bottom: 24px; }
        .leave-form-grid  { display: grid; grid-template-columns: 1fr; gap: 24px; }
        .leave-date-row   { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
        @media (min-width: 640px) {
          .leave-type-grid { grid-template-columns: repeat(4, 1fr); }
          .leave-form-grid { grid-template-columns: 1fr 1fr; }
        }
        .leave-type-grid > div + div { border-left: 2px solid ${t.border}; }
        @media (max-width: 639px) { .leave-type-grid > div:nth-child(2n) { border-left: 2px solid ${t.border}; } .leave-type-grid > div:nth-child(n+3) { border-top: 2px solid ${t.border}; } }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 9, letterSpacing: '3px', color: t.accent, fontWeight: 700, marginBottom: 6 }}>LEAVE MANAGEMENT</div>
        <div style={{ fontSize: 'clamp(22px, 6vw, 32px)', fontWeight: 900, letterSpacing: '-2px', color: t.text }}>MY LEAVE.</div>
      </div>

      {/* Leave type cards */}
      <div className="leave-type-grid">
        {Object.keys(LEAVE_TYPES).map(type => (
          <LeaveTypeCard
            key={type}
            type={type}
            balance={leaveBalance[type] || { balance: 0, total: 0 }}
            selected={selectedType === type}
            onClick={setSelectedType}
            theme={t}
          />
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: `2px solid ${t.border}`, marginBottom: 20 }}>
        {[['apply','APPLY FOR LEAVE'],['history','MY HISTORY']].map(([key, label]) => (
          <div
            key={key}
            onClick={() => setTab(key)}
            style={{
              padding: '10px 18px', fontSize: 9, letterSpacing: '2px', fontWeight: 700,
              cursor: 'pointer', color: tab === key ? t.text : t.textMuted,
              borderBottom: tab === key ? `2px solid ${t.accent}` : '2px solid transparent',
              marginBottom: -2,
            }}
          >
            {label}
          </div>
        ))}
      </div>

      {tab === 'apply' && (
        <div className="leave-form-grid">
          {/* Form */}
          <div>
            <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: 20 }}>
              {/* Type info banner */}
              <div style={{ background: t.surface, border: `2px solid ${LEAVE_TYPES[selectedType].color}`, padding: 12, marginBottom: 18 }}>
                <div style={{ fontSize: 8, letterSpacing: '2px', fontWeight: 700, color: LEAVE_TYPES[selectedType].color, marginBottom: 5 }}>
                  {LEAVE_TYPES[selectedType].code} — {LEAVE_TYPES[selectedType].fullName.toUpperCase()}
                </div>
                <div style={{ fontSize: 11, color: t.textSub, lineHeight: 1.6 }}>{LEAVE_TYPES[selectedType].description}</div>
                {LEAVE_TYPES[selectedType].requiresCertificate && (
                  <div style={{ fontSize: 10, color: t.warning, marginTop: 6, fontWeight: 700 }}>⚠ MEDICAL CERTIFICATE MAY BE REQUIRED</div>
                )}
              </div>

              {/* Type select */}
              <div style={{ marginBottom: 14 }}>
                <label style={lbl}>LEAVE TYPE</label>
                <select value={selectedType} onChange={e => setSelectedType(e.target.value)} style={inp}>
                  {Object.entries(LEAVE_TYPES).map(([k, v]) => (
                    <option key={k} value={k}>{v.code} — {v.name} ({leaveBalance[k]?.balance || 0} days left)</option>
                  ))}
                </select>
              </div>

              {/* Date row */}
              <div className="leave-date-row">
                <div>
                  <label style={lbl}>FROM DATE</label>
                  <input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} min={format(new Date(), 'yyyy-MM-dd')} style={inp} />
                </div>
                <div>
                  <label style={lbl}>TO DATE</label>
                  <input type="date" value={toDate} onChange={e => setToDate(e.target.value)} min={fromDate || format(new Date(), 'yyyy-MM-dd')} style={inp} />
                </div>
              </div>

              {workingDays > 0 && (
                <div style={{ background: t.surface, border: `2px solid ${t.border}`, padding: '10px 14px', marginBottom: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 9, color: t.textMuted, letterSpacing: '1px' }}>WORKING DAYS</span>
                  <span style={{ fontSize: 18, fontWeight: 900, color: t.accent }}>{workingDays}</span>
                </div>
              )}

              <div style={{ marginBottom: 18 }}>
                <label style={lbl}>REASON</label>
                <textarea value={reason} onChange={e => setReason(e.target.value)} rows={3}
                  placeholder="Briefly describe your reason for leave..."
                  style={{ ...inp, resize: 'vertical', lineHeight: 1.6 }} />
              </div>

              {(selectedType === 'ML' || selectedType === 'SL') && (
                <div style={{ marginBottom: 18 }}>
                  <label style={lbl}>
                    MEDICAL CERTIFICATE 
                    {(selectedType === 'ML' || (selectedType === 'SL' && workingDays >= 3)) && (
                      <span style={{ color: t.danger, marginLeft: 4 }}>* MANDATORY</span>
                    )}
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="file" 
                      accept="image/*,.pdf" 
                      onChange={handleFileChange}
                      style={{ ...inp, opacity: 0, position: 'absolute', inset: 0, cursor: 'pointer', zIndex: 2 }} 
                    />
                    <div style={{ 
                      ...inp, display: 'flex', alignItems: 'center', justifyContent: 'center', 
                      background: t.card, borderStyle: 'dashed', color: certFileName ? t.accent : t.textMuted,
                      borderColor: (needsCert && !medicalCert) ? t.danger : t.border
                    }}>
                      {certFileName || 'Upload Certificate (Image/PDF)'}
                    </div>
                  </div>
                  <p style={{ fontSize: 9, color: t.textMuted, marginTop: 4 }}>Max Size: 2MB</p>
                </div>
              )}

              <button
                onClick={handleApply}
                disabled={submitting || !fromDate || !toDate || !reason}
                style={{
                  width: '100%', padding: '13px', background: submitting ? t.border : t.accent,
                  border: 'none', color: '#fff', fontSize: 9, letterSpacing: '3px',
                  fontWeight: 900, cursor: submitting ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
                }}
              >
                {submitting ? 'SUBMITTING...' : 'SUBMIT APPLICATION'}
              </button>
            </div>
          </div>

          {/* Policy summary */}
          <div>
            <div style={{ fontSize: 8, letterSpacing: '3px', color: t.textMuted, fontWeight: 700, marginBottom: 12 }}>LEAVE POLICY</div>
            {Object.entries(LEAVE_TYPES).map(([type, info]) => (
              <div key={type} style={{ background: t.card, border: `2px solid ${t.border}`, borderLeft: `4px solid ${info.color}`, padding: '12px 14px', marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5, flexWrap: 'wrap', gap: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: t.text }}>{info.fullName}</span>
                  <span style={{ fontSize: 11, fontWeight: 900, color: info.color }}>{info.totalPerYear}d/yr</span>
                </div>
                <div style={{ fontSize: 9, color: t.textMuted, lineHeight: 1.6 }}>
                  {info.accrualRate} · Carry: {info.carryForward > 0 ? `${info.carryForward}d` : 'None'} · Encashable: {info.encashable ? 'Yes' : 'No'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'history' && (
        <div>
          {loading ? (
            <div style={{ color: t.textMuted, fontSize: 11, letterSpacing: '2px' }}>LOADING...</div>
          ) : leaves.length === 0 ? (
            <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: 40, textAlign: 'center' }}>
              <div style={{ fontSize: 10, color: t.textMuted, letterSpacing: '2px' }}>NO LEAVE APPLICATIONS YET</div>
            </div>
          ) : (
            <div style={{ background: t.card, border: `2px solid ${t.border}` }}>
              {leaves.map((leave, i) => {
                const info        = LEAVE_TYPES[leave.leave_type]
                const statusColor = STATUS_COLORS[leave.status] || t.textMuted
                return (
                  <div key={leave.id} style={{
                    padding: '14px 16px', borderBottom: i < leaves.length - 1 ? `1px solid ${t.border}` : 'none',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10,
                  }}>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', flex: 1, minWidth: 0 }}>
                      <div style={{ width: 4, alignSelf: 'stretch', background: info?.color || t.border, flexShrink: 0 }} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color: t.text }}>
                          {info?.name || leave.leave_type} — {leave.days_requested || 1} day{(leave.days_requested || 1) > 1 ? 's' : ''}
                        </div>
                        <div style={{ fontSize: 10, color: t.textMuted, marginTop: 2 }}>{leave.from_date} → {leave.to_date}</div>
                        <div style={{ fontSize: 10, color: t.textSub, marginTop: 2, fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 260 }}>
                          {leave.reason}
                        </div>
                        {leave.admin_response && (
                          <div style={{ fontSize: 10, color: statusColor, marginTop: 3 }}>Admin: {leave.admin_response}</div>
                        )}
                        {/* Thread rendering */}
                        {leave.comments && leave.comments.length > 0 && (
                          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {leave.comments.map((c, idx) => (
                              <div key={idx} style={{
                                padding: 8, borderRadius: 4, border: `1px solid ${c.sender === 'employee' ? t.border : 'rgba(51, 181, 229, 0.3)'}`,
                                fontSize: 10, fontFamily: 'monospace', maxWidth: '90%',
                                alignSelf: c.sender === 'employee' ? 'flex-end' : 'flex-start',
                                background: c.sender === 'employee' ? t.surface : 'rgba(51, 181, 229, 0.1)',
                                color: c.sender === 'employee' ? t.text : '#33b5e5'
                              }}>
                                <div style={{ opacity: 0.5, fontSize: 8, marginBottom: 2 }}>
                                  {c.sender === 'employee' ? 'You' : 'Admin'} • {new Date(c.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                </div>
                                {c.message}
                              </div>
                            ))}
                          </div>
                        )}
                        {/* Reply box if needs_info */}
                        {leave.status === 'needs_info' && (
                          <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                            <input 
                              type="text" 
                              placeholder="Type your reply here..." 
                              value={replyText[leave.id] || ''}
                              onChange={e => setReplyText(prev => ({ ...prev, [leave.id]: e.target.value }))}
                              style={{ ...inp, padding: '7px 10px', fontSize: 11, flex: 1 }}
                            />
                            <button
                              onClick={() => handleReply(leave.id)}
                              disabled={replying === leave.id}
                              style={{ 
                                background: 'transparent', border: '1px solid #33b5e5', color: '#33b5e5', fontWeight: 700, 
                                fontSize: 10, padding: '0 12px', cursor: replying === leave.id ? 'wait' : 'pointer' 
                              }}
                            >
                              {replying === leave.id ? '...' : 'REPLY'}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ fontSize: 8, letterSpacing: '1px', fontWeight: 700, color: statusColor, background: statusColor + '20', padding: '5px 10px', flexShrink: 0, whiteSpace: 'nowrap' }}>
                      {leave.status.replace('_', ' ').toUpperCase()}
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