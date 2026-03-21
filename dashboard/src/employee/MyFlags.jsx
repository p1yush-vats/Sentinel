import { useState, useEffect } from 'react'
import { useTheme } from './ThemeContext'
import { flagsAPI, appealsAPI } from '../services/api'
import api from '../services/api'
import toast from 'react-hot-toast'
import { fromNow } from '../utils/helpers'

const FLAG_EXPLANATIONS = {
  mechanical_typing: {
    title: 'Very Consistent Typing Pattern',
    plain: 'Our system noticed your keystrokes were unusually consistent in timing — more like a metronome than natural typing. This can sometimes be triggered by auto-complete tools or macros.',
    severity: 'medium',
    tip: 'If you use text expansion tools or auto-complete software, mention that in your appeal.',
  },
  long_idle: {
    title: 'Extended Away From Keyboard',
    plain: 'You were logged in and working, but there was no keyboard or mouse activity for a significant period. This could be a meeting, a phone call, reading documents, or stepping away.',
    severity: 'low',
    tip: 'Mention what you were doing during this period (e.g., in a meeting, on a call, reviewing printed documents).',
  },
  rapid_paste: {
    title: 'Multiple Pastes in Quick Succession',
    plain: 'Several paste operations were detected in a short time window. This is common when formatting documents, moving content between files, or working with code.',
    severity: 'low',
    tip: 'Explain the context — e.g., migrating data, formatting a report, or code refactoring.',
  },
  suspicious_paste: {
    title: 'Large Content Paste Detected',
    plain: 'A very large block of text was pasted at once. This can happen when copying reports, documentation, code files, or data from external sources.',
    severity: 'medium',
    tip: 'Describe what you were working on and why you needed to paste large amounts of content.',
  },
  mouse_jiggler: {
    title: 'Regular Mouse Movement Pattern',
    plain: 'Mouse movements were detected at very regular intervals, which can indicate anti-idle software. However this can also be caused by certain accessibility tools or touchpad drivers.',
    severity: 'high',
    tip: 'If you use any accessibility tools, system utilities, or have a dual-monitor setup, mention these.',
  },
  clock_in_clock_out: {
    title: 'Session Started But Minimal Activity',
    plain: 'Your session was started but very little keyboard or mouse activity was recorded afterwards. This might happen if you got pulled into something immediately after logging in.',
    severity: 'medium',
    tip: 'Explain what you were doing right after clocking in — e.g., a meeting, phone call, or other offline task.',
  },
  burst_then_idle: {
    title: 'Activity Then Long Silence',
    plain: 'A flurry of activity was detected followed by a long period of no input. This is normal if you completed a task and then moved to offline work, meetings, or reading.',
    severity: 'low',
    tip: 'Note what you were doing in the quiet period.',
  },
  minimal_activity: {
    title: 'Very Low Keyboard Activity',
    plain: 'Fewer keystrokes than expected were recorded during your session. This can happen during tasks that involve more reading, thinking, or meetings than typing.',
    severity: 'low',
    tip: 'Describe the nature of your work that day.',
  },
  superhuman_speed: {
    title: 'Unusually Fast Typing Speed',
    plain: 'Typing speed exceeded what is normally humanly possible for a sustained period. This is often caused by auto-fill, text expansion tools, or copy-paste from formatted sources.',
    severity: 'high',
    tip: 'Mention any text expansion tools, IDE auto-complete, or other productivity software you use.',
  },
}

const SEVERITY_COLORS = {
  low: '#ffbb00',
  medium: '#ff8800',
  high: '#ff4444',
  critical: '#cc0000',
  LOW: '#ffbb00',
  MEDIUM: '#ff8800',
  HIGH: '#ff4444',
  CRITICAL: '#cc0000',
}

export default function MyFlags() {
  const { theme } = useTheme()
  const [flags, setFlags] = useState([])
  const [appeals, setAppeals] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [appealText, setAppealText] = useState({})
  const [submitting, setSubmitting] = useState(null)

  useEffect(() => {
    Promise.all([
      api.get('/abnormalities/'),
      api.get('/appeals/'),
    ]).then(([fRes, aRes]) => {
      setFlags(fRes.data?.abnormalities || [])
      setAppeals(aRes.data?.appeals || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const hasAppeal = (flagId) => appeals.some(a => a.abnormality_id === flagId)
  const getAppeal = (flagId) => appeals.find(a => a.abnormality_id === flagId)

  const submitAppeal = async (flag) => {
    const reason = appealText[flag.id]
    if (!reason?.trim()) { toast.error('Please write your explanation'); return }
    setSubmitting(flag.id)
    try {
      await api.post('/appeals/', {
        session_id: flag.session_id,
        abnormality_id: flag.id,
        reason,
      })
      toast.success('Appeal submitted successfully')
      const aRes = await api.get('/appeals/')
      setAppeals(aRes.data?.appeals || [])
      setAppealText(prev => ({ ...prev, [flag.id]: '' }))
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to submit appeal')
    } finally {
      setSubmitting(null)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '32px' }}>
        <div style={{ fontSize: '9px', letterSpacing: '3px', color: theme.accent, fontWeight: '700', marginBottom: '8px' }}>FLAGS & APPEALS</div>
        <div style={{ fontSize: '32px', fontWeight: '900', letterSpacing: '-2px', color: theme.text }}>MY FLAGS.</div>
        <div style={{ fontSize: '11px', color: theme.textMuted, marginTop: '8px', maxWidth: '500px', lineHeight: 1.6 }}>
          Flags are raised automatically when patterns in your work session seem unusual.
          They are not accusations — they are prompts for review. You can submit an appeal for any flag.
        </div>
      </div>

      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0', marginBottom: '24px', border: `2px solid ${theme.border}` }}>
        {[
          { label: 'TOTAL FLAGS', value: flags.length, color: theme.text },
          { label: 'PENDING REVIEW', value: flags.filter(f => !f.reviewed).length, color: theme.warning },
          { label: 'APPEALS FILED', value: appeals.length, color: theme.info },
        ].map((s, i) => (
          <div key={i} style={{ padding: '20px', background: theme.card, borderRight: i < 2 ? `2px solid ${theme.border}` : 'none', textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: '900', color: s.color }}>{s.value}</div>
            <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, marginTop: '4px' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {loading ? (
        <div style={{ color: theme.textMuted, fontSize: '11px', letterSpacing: '2px' }}>LOADING...</div>
      ) : flags.length === 0 ? (
        <div style={{ background: theme.card, border: `2px solid ${theme.border}`, padding: '60px', textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>✓</div>
          <div style={{ fontSize: '14px', fontWeight: '900', color: theme.success, letterSpacing: '-0.5px' }}>ALL CLEAR</div>
          <div style={{ fontSize: '10px', color: theme.textMuted, marginTop: '8px', letterSpacing: '1px' }}>NO FLAGS ON YOUR ACCOUNT</div>
        </div>
      ) : (
        <div>
          {flags.map((flag, i) => {
            const types = Object.keys(flag.detections || {})
            const primaryType = types[0]
            const explanation = FLAG_EXPLANATIONS[primaryType]
            const isExp = expanded === flag.id
            const appeal = getAppeal(flag.id)
            const alreadyAppealed = hasAppeal(flag.id)
            const sevColor = SEVERITY_COLORS[flag.overall_severity] || theme.warning

            return (
              <div key={flag.id} style={{
                background: theme.card,
                border: `2px solid ${theme.border}`,
                borderLeft: `4px solid ${sevColor}`,
                marginBottom: '8px',
              }}>
                {/* Flag header */}
                <div
                  onClick={() => setExpanded(isExp ? null : flag.id)}
                  style={{ padding: '16px 20px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: '700', color: theme.text, marginBottom: '4px' }}>
                      {explanation?.title || primaryType?.replace(/_/g, ' ')?.toUpperCase()}
                    </div>
                    <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '9px', letterSpacing: '1px', fontWeight: '700', color: sevColor }}>
                        {flag.overall_severity}
                      </span>
                      <span style={{ fontSize: '9px', color: theme.textMuted }}>
                        {Math.round((flag.confidence_score || 0) * 100)}% CONFIDENCE
                      </span>
                      <span style={{ fontSize: '9px', color: theme.textMuted }}>
                        {fromNow(flag.first_detected_at)}
                      </span>
                      {flag.reviewed && (
                        <span style={{ fontSize: '9px', color: theme.success, fontWeight: '700' }}>
                          ✓ REVIEWED — {flag.review_decision?.toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    {alreadyAppealed && (
                      <span style={{ fontSize: '9px', letterSpacing: '1px', color: theme.info, fontWeight: '700' }}>
                        APPEAL {appeal?.status?.toUpperCase()}
                      </span>
                    )}
                    <span style={{ fontSize: '12px', color: theme.textMuted }}>{isExp ? '▲' : '▼'}</span>
                  </div>
                </div>

                {/* Expanded */}
                {isExp && (
                  <div style={{ padding: '0 20px 20px', borderTop: `1px solid ${theme.border}` }}>

                    {/* Plain English explanation */}
                    {explanation && (
                      <div style={{ background: theme.surface, padding: '16px', marginTop: '16px', marginBottom: '16px' }}>
                        <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700', marginBottom: '8px' }}>WHAT DOES THIS MEAN?</div>
                        <div style={{ fontSize: '12px', color: theme.textSub, lineHeight: 1.7 }}>{explanation.plain}</div>
                        <div style={{ marginTop: '10px', fontSize: '11px', color: theme.info, lineHeight: 1.6 }}>
                          <strong style={{ fontWeight: '700' }}>TIP:</strong> {explanation.tip}
                        </div>
                      </div>
                    )}

                    {/* Detection details */}
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700', marginBottom: '8px' }}>DETECTION DETAILS</div>
                      {types.map(t => {
                        const d = flag.detections[t]
                        return (
                          <div key={t} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: `1px solid ${theme.border}` }}>
                            <span style={{ fontSize: '10px', color: theme.text }}>{t.replace(/_/g, ' ')}</span>
                            <span style={{ fontSize: '10px', color: theme.textMuted }}>
                              {d.occurrences}× · {Math.round((d.confidence || 0) * 100)}% · {d.severity}
                            </span>
                          </div>
                        )
                      })}
                    </div>

                    {/* Appeal section */}
                    {!flag.reviewed && !alreadyAppealed && (
                      <div>
                        <div style={{ fontSize: '9px', letterSpacing: '2px', color: theme.textMuted, fontWeight: '700', marginBottom: '10px' }}>SUBMIT AN APPEAL</div>
                        <textarea
                          value={appealText[flag.id] || ''}
                          onChange={e => setAppealText(prev => ({ ...prev, [flag.id]: e.target.value }))}
                          placeholder="Explain what you were doing during this session. The more context you provide, the easier it is for the admin to review your appeal..."
                          rows={4}
                          style={{
                            width: '100%',
                            background: theme.surface,
                            border: `2px solid ${theme.border}`,
                            color: theme.text,
                            padding: '12px',
                            fontSize: '12px',
                            fontFamily: 'inherit',
                            resize: 'vertical',
                            outline: 'none',
                            lineHeight: 1.6,
                            boxSizing: 'border-box',
                          }}
                        />
                        <button
                          onClick={() => submitAppeal(flag)}
                          disabled={submitting === flag.id}
                          style={{
                            marginTop: '10px',
                            padding: '12px 24px',
                            background: submitting === flag.id ? theme.border : theme.accent,
                            border: 'none',
                            color: '#fff',
                            fontSize: '9px',
                            letterSpacing: '3px',
                            fontWeight: '900',
                            cursor: submitting === flag.id ? 'not-allowed' : 'pointer',
                            fontFamily: 'inherit',
                          }}
                        >
                          {submitting === flag.id ? 'SUBMITTING...' : 'SUBMIT APPEAL'}
                        </button>
                      </div>
                    )}

                    {alreadyAppealed && appeal && (
                      <div style={{ background: theme.surface, border: `2px solid ${theme.border}`, padding: '14px' }}>
                        <div style={{ fontSize: '9px', letterSpacing: '2px', fontWeight: '700', color: theme.info, marginBottom: '8px' }}>YOUR APPEAL — {appeal.status?.toUpperCase()}</div>
                        <div style={{ fontSize: '11px', color: theme.textSub, lineHeight: 1.6 }}>{appeal.reason}</div>
                        {appeal.admin_response && (
                          <div style={{ marginTop: '10px', padding: '10px', background: theme.card, borderLeft: `3px solid ${theme.success}` }}>
                            <div style={{ fontSize: '9px', color: theme.success, fontWeight: '700', marginBottom: '4px' }}>ADMIN RESPONSE</div>
                            <div style={{ fontSize: '11px', color: theme.text }}>{appeal.admin_response}</div>
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
