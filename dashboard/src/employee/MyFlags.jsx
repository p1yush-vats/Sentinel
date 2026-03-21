import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { flagsAPI, appealsAPI } from '../services/api'
import api from '../services/api'
import toast from 'react-hot-toast'
import { fromNow } from '../utils/helpers'

const FLAG_EXPLANATIONS = {
  mechanical_typing:  { title: 'Very Consistent Typing Pattern',     plain: 'Your keystrokes were unusually consistent in timing — more like a metronome than natural typing. This can be triggered by auto-complete tools or macros.',            tip: 'If you use text expansion tools or auto-complete, mention that in your appeal.' },
  long_idle:          { title: 'Extended Away From Keyboard',         plain: 'No keyboard or mouse activity was detected for a significant period. This could be a meeting, phone call, or stepping away.',                                           tip: 'Mention what you were doing during this period (e.g., in a meeting, on a call).' },
  rapid_paste:        { title: 'Multiple Pastes in Quick Succession', plain: 'Several paste operations were detected in a short window. Common when formatting documents, moving content, or working with code.',                                    tip: 'Explain the context — e.g., migrating data or code refactoring.' },
  suspicious_paste:   { title: 'Large Content Paste Detected',        plain: 'A very large block of text was pasted at once. This can happen when copying reports, documentation, or code files.',                                                   tip: 'Describe what you were working on and why you needed to paste large content.' },
  mouse_jiggler:      { title: 'Regular Mouse Movement Pattern',       plain: 'Mouse movements were detected at very regular intervals, which can indicate anti-idle software. However this can also be caused by accessibility tools or touchpad drivers.', tip: 'If you use accessibility tools or have a dual-monitor setup, mention these.' },
  clock_in_clock_out: { title: 'Session Started But Minimal Activity', plain: 'Your session was started but very little keyboard or mouse activity was recorded. This might happen if you got pulled into something immediately after logging in.',     tip: 'Explain what you were doing right after clocking in.' },
  burst_then_idle:    { title: 'Activity Then Long Silence',           plain: 'A flurry of activity was detected followed by a long period of no input. Normal if you completed a task and moved to offline work or meetings.',                        tip: 'Note what you were doing in the quiet period.' },
  minimal_activity:   { title: 'Very Low Keyboard Activity',           plain: 'Fewer keystrokes than expected were recorded. This can happen during tasks involving more reading, thinking, or meetings than typing.',                                  tip: 'Describe the nature of your work that day.' },
  superhuman_speed:   { title: 'Unusually Fast Typing Speed',          plain: 'Typing speed exceeded what is normally humanly possible. Often caused by auto-fill, text expansion tools, or copy-paste from formatted sources.',                      tip: 'Mention any text expansion tools, IDE auto-complete, or other productivity software.' },
}

const SEVERITY_COLORS = {
  low: '#ffbb00', medium: '#ff8800', high: '#ff4444', critical: '#cc0000',
  LOW: '#ffbb00', MEDIUM: '#ff8800', HIGH: '#ff4444', CRITICAL: '#cc0000',
}

export default function MyFlags() {
  const { theme } = useTheme()
  const [flags,       setFlags]       = useState([])
  const [appeals,     setAppeals]     = useState([])
  const [loading,     setLoading]     = useState(true)
  const [expanded,    setExpanded]    = useState(null)
  const [appealText,  setAppealText]  = useState({})
  const [submitting,  setSubmitting]  = useState(null)
  const t = theme

  useEffect(() => {
    Promise.all([api.get('/abnormalities/'), api.get('/appeals/')])
      .then(([fRes, aRes]) => {
        setFlags(fRes.data?.abnormalities || [])
        setAppeals(aRes.data?.appeals || [])
      }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const hasAppeal = (id) => appeals.some(a => a.abnormality_id === id)
  const getAppeal = (id) => appeals.find(a => a.abnormality_id === id)

  const submitAppeal = async (flag) => {
    const reason = appealText[flag.id]
    if (!reason?.trim()) { toast.error('Please write your explanation'); return }
    setSubmitting(flag.id)
    try {
      await api.post('/appeals/', { session_id: flag.session_id, abnormality_id: flag.id, reason })
      toast.success('Appeal submitted successfully')
      const aRes = await api.get('/appeals/')
      setAppeals(aRes.data?.appeals || [])
      setAppealText(prev => ({ ...prev, [flag.id]: '' }))
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to submit appeal')
    } finally { setSubmitting(null) }
  }

  return (
    <div>
      <style>{`
        .flags-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); }
        @media (max-width: 480px) { .flags-grid-3 { grid-template-columns: repeat(3, 1fr); } }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 9, letterSpacing: '3px', color: t.accent, fontWeight: 700, marginBottom: 6 }}>FLAGS & APPEALS</div>
        <div style={{ fontSize: 'clamp(22px, 6vw, 32px)', fontWeight: 900, letterSpacing: '-2px', color: t.text }}>MY FLAGS.</div>
        <div style={{ fontSize: 11, color: t.textMuted, marginTop: 8, maxWidth: 500, lineHeight: 1.6 }}>
          Flags are raised when patterns in your session seem unusual. They are not accusations — you can appeal any flag.
        </div>
      </div>

      {/* Summary */}
      <div className="flags-grid-3" style={{ marginBottom: 20, border: `2px solid ${t.border}` }}>
        {[
          { label: 'TOTAL FLAGS',    value: flags.length,                          color: t.text },
          { label: 'PENDING REVIEW', value: flags.filter(f => !f.reviewed).length, color: t.warning },
          { label: 'APPEALS FILED',  value: appeals.length,                        color: t.info },
        ].map((s, i) => (
          <div key={i} style={{ padding: '16px 10px', background: t.card, borderRight: i < 2 ? `2px solid ${t.border}` : 'none', textAlign: 'center' }}>
            <div style={{ fontSize: 'clamp(22px, 5vw, 30px)', fontWeight: 900, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 8, letterSpacing: '1.5px', color: t.textMuted, marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ color: t.textMuted, fontSize: 11, letterSpacing: '2px' }}>LOADING...</div>
      ) : flags.length === 0 ? (
        <div style={{ background: t.card, border: `2px solid ${t.border}`, padding: '48px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: 28, marginBottom: 10 }}>✓</div>
          <div style={{ fontSize: 14, fontWeight: 900, color: t.success, letterSpacing: '-0.5px' }}>ALL CLEAR</div>
          <div style={{ fontSize: 10, color: t.textMuted, marginTop: 8, letterSpacing: '1px' }}>NO FLAGS ON YOUR ACCOUNT</div>
        </div>
      ) : (
        <div>
          {flags.map((flag) => {
            const types       = Object.keys(flag.detections || {})
            const primaryType = types[0]
            const explanation = FLAG_EXPLANATIONS[primaryType]
            const isExp       = expanded === flag.id
            const appeal      = getAppeal(flag.id)
            const alreadyAppealed = hasAppeal(flag.id)
            const sevColor    = SEVERITY_COLORS[flag.overall_severity] || t.warning

            return (
              <div key={flag.id} style={{
                background: t.card,
                border: `2px solid ${t.border}`,
                borderLeft: `4px solid ${sevColor}`,
                marginBottom: 8,
              }}>
                {/* Header */}
                <div
                  onClick={() => setExpanded(isExp ? null : flag.id)}
                  style={{ padding: '14px 16px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: t.text, marginBottom: 5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {explanation?.title || primaryType?.replace(/_/g, ' ')?.toUpperCase()}
                    </div>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 8, letterSpacing: '1px', fontWeight: 700, color: sevColor }}>{flag.overall_severity}</span>
                      <span style={{ fontSize: 8, color: t.textMuted }}>{Math.round((flag.confidence_score || 0) * 100)}% CONF</span>
                      <span style={{ fontSize: 8, color: t.textMuted }}>{fromNow(flag.first_detected_at)}</span>
                      {flag.reviewed && (
                        <span style={{ fontSize: 8, color: t.success, fontWeight: 700 }}>✓ {flag.review_decision?.toUpperCase()}</span>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexShrink: 0 }}>
                    {alreadyAppealed && (
                      <span style={{ fontSize: 8, letterSpacing: '1px', color: t.info, fontWeight: 700 }}>
                        {appeal?.status?.toUpperCase()}
                      </span>
                    )}
                    <span style={{ fontSize: 12, color: t.textMuted }}>{isExp ? '▲' : '▼'}</span>
                  </div>
                </div>

                {/* Expanded */}
                {isExp && (
                  <div style={{ padding: '0 16px 16px', borderTop: `1px solid ${t.border}` }}>
                    {explanation && (
                      <div style={{ background: t.surface, padding: 14, marginTop: 14, marginBottom: 14 }}>
                        <div style={{ fontSize: 8, letterSpacing: '2px', color: t.textMuted, fontWeight: 700, marginBottom: 8 }}>WHAT DOES THIS MEAN?</div>
                        <div style={{ fontSize: 12, color: t.textSub, lineHeight: 1.7 }}>{explanation.plain}</div>
                        <div style={{ marginTop: 10, fontSize: 11, color: t.info, lineHeight: 1.6 }}>
                          <strong style={{ fontWeight: 700 }}>TIP:</strong> {explanation.tip}
                        </div>
                      </div>
                    )}

                    {/* Detection details */}
                    <div style={{ marginBottom: 14 }}>
                      <div style={{ fontSize: 8, letterSpacing: '2px', color: t.textMuted, fontWeight: 700, marginBottom: 8 }}>DETECTION DETAILS</div>
                      {types.map(tp => {
                        const d = flag.detections[tp]
                        return (
                          <div key={tp} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: `1px solid ${t.border}`, gap: 8, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: 10, color: t.text }}>{tp.replace(/_/g, ' ')}</span>
                            <span style={{ fontSize: 9, color: t.textMuted }}>
                              {d.occurrences}× · {Math.round((d.confidence || 0) * 100)}% · {d.severity}
                            </span>
                          </div>
                        )
                      })}
                    </div>

                    {/* Appeal form */}
                    {!flag.reviewed && !alreadyAppealed && (
                      <div>
                        <div style={{ fontSize: 8, letterSpacing: '2px', color: t.textMuted, fontWeight: 700, marginBottom: 10 }}>SUBMIT AN APPEAL</div>
                        <textarea
                          value={appealText[flag.id] || ''}
                          onChange={e => setAppealText(prev => ({ ...prev, [flag.id]: e.target.value }))}
                          placeholder="Explain what you were doing during this session..."
                          rows={4}
                          style={{
                            width: '100%', background: t.surface, border: `2px solid ${t.border}`,
                            color: t.text, padding: 12, fontSize: 12, fontFamily: 'inherit',
                            resize: 'vertical', outline: 'none', lineHeight: 1.6, boxSizing: 'border-box',
                          }}
                        />
                        <button
                          onClick={() => submitAppeal(flag)}
                          disabled={submitting === flag.id}
                          style={{
                            marginTop: 10, padding: '11px 20px',
                            background: submitting === flag.id ? t.border : t.accent,
                            border: 'none', color: '#fff', fontSize: 9, letterSpacing: '3px',
                            fontWeight: 900, cursor: submitting === flag.id ? 'not-allowed' : 'pointer',
                            fontFamily: 'inherit',
                          }}
                        >
                          {submitting === flag.id ? 'SUBMITTING...' : 'SUBMIT APPEAL'}
                        </button>
                      </div>
                    )}

                    {alreadyAppealed && appeal && (
                      <div style={{ background: t.surface, border: `2px solid ${t.border}`, padding: 14 }}>
                        <div style={{ fontSize: 8, letterSpacing: '2px', fontWeight: 700, color: t.info, marginBottom: 8 }}>YOUR APPEAL — {appeal.status?.toUpperCase()}</div>
                        <div style={{ fontSize: 11, color: t.textSub, lineHeight: 1.6 }}>{appeal.reason}</div>
                        {appeal.admin_response && (
                          <div style={{ marginTop: 10, padding: 10, background: t.card, borderLeft: `3px solid ${t.success}` }}>
                            <div style={{ fontSize: 8, color: t.success, fontWeight: 700, marginBottom: 4 }}>ADMIN RESPONSE</div>
                            <div style={{ fontSize: 11, color: t.text }}>{appeal.admin_response}</div>
                          </div>
                        )}
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