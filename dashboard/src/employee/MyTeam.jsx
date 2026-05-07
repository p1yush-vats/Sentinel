import { useState, useEffect, useRef, useCallback } from 'react'
import { useTheme } from './ThemeContext'
import { useAuthStore } from '../store/authStore'
import { employeesAPI, chatAPI, dmAPI } from '../services/api'
import { Users, MessageSquare, Send, Wifi, WifiOff, Circle, RefreshCw, Pin, X, ArrowLeft, Mail } from 'lucide-react'

// ─── helpers ────────────────────────────────────────────────────────────────
const initials = (name) =>
  name?.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2) || '??'

const fmtTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h ago`
  return d.toLocaleDateString()
}

const AVATAR_COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b',
  '#10b981', '#3b82f6', '#ef4444', '#14b8a6',
]
const avatarColor = (name) =>
  AVATAR_COLORS[(name?.charCodeAt(0) || 0) % AVATAR_COLORS.length]

// ─── Member Card ─────────────────────────────────────────────────────────────
function MemberCard({ member, t, onDm }) {
  const [imgErr, setImgErr] = useState(false)
  const bg = avatarColor(member.full_name)
  return (
    <div
      style={{
        background: t.card,
        border: `1.5px solid ${t.border}`,
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        transition: 'border-color 0.15s',
        position: 'relative',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = t.accent)}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = t.border)}
    >
      {/* Avatar */}
      <div
        style={{
          width: 44,
          height: 44,
          background: bg,
          borderRadius: '50%',
          flexShrink: 0,
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 15,
          fontWeight: 900,
          color: '#fff',
          position: 'relative',
        }}
      >
        {member.avatar_url && !imgErr ? (
          <img
            src={member.avatar_url}
            alt=""
            onError={() => setImgErr(true)}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          initials(member.full_name)
        )}
        {/* Online dot */}
        <span
          style={{
            position: 'absolute',
            bottom: 1,
            right: 1,
            width: 11,
            height: 11,
            borderRadius: '50%',
            background: member.is_online ? '#22c55e' : t.textMuted,
            border: `2px solid ${t.card}`,
          }}
        />
      </div>

      <div style={{ minWidth: 0 }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: t.text,
            letterSpacing: '-0.3px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {member.full_name}
        </div>
        <div style={{ fontSize: 9, color: t.textMuted, letterSpacing: '1px', marginTop: 3 }}>
          {member.position || 'Employee'}
        </div>
        <div
          style={{
            fontSize: 8,
            marginTop: 4,
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            color: member.is_online ? '#22c55e' : t.textMuted,
            letterSpacing: '1px',
          }}
        >
          <Circle size={6} fill={member.is_online ? '#22c55e' : 'currentColor'} />
          {member.is_online ? 'ONLINE' : 'OFFLINE'}
        </div>
      </div>

      {/* DM button */}
      {onDm && (
        <button onClick={() => onDm(member)} title={`Message ${member.full_name}`} style={{
          marginLeft: 'auto', background: 'transparent', border: `1px solid ${t.border}`,
          color: t.textMuted, cursor: 'pointer', padding: '6px', display: 'flex',
          alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = t.accent; e.currentTarget.style.color = t.accent }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = t.border; e.currentTarget.style.color = t.textMuted }}
        >
          <Mail size={14} />
        </button>
      )}
    </div>
  )
}

// ─── Render @mentions ────────────────────────────────────────────────────────
function RenderContent({ text, t }) {
  const parts = text.split(/(@\w+)/g)
  return <>{parts.map((p, i) =>
    p.startsWith('@') ? <span key={i} style={{ background: '#facc1522', color: '#facc15', fontWeight: 700, padding: '1px 4px', borderRadius: 2 }}>{p}</span> : p
  )}</>
}

// ─── Chat Bubble ─────────────────────────────────────────────────────────────
function ChatBubble({ msg, isMe, t, onPin }) {
  const [imgErr, setImgErr] = useState(false)
  const [hover, setHover] = useState(false)
  const bg = avatarColor(msg.sender_name)
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isMe ? 'row-reverse' : 'row',
        gap: 8,
        alignItems: 'flex-end',
        marginBottom: 10,
        position: 'relative',
      }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div
        style={{
          width: 28, height: 28, borderRadius: '50%', background: bg,
          overflow: 'hidden', flexShrink: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          fontSize: 10, fontWeight: 700, color: '#fff',
        }}
      >
        {msg.sender_avatar && !imgErr ? (
          <img src={msg.sender_avatar} alt="" onError={() => setImgErr(true)}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : initials(msg.sender_name)}
      </div>

      <div style={{ maxWidth: '72%' }}>
        {!isMe && (
          <div style={{ fontSize: 8, color: t.textMuted, letterSpacing: '1px', marginBottom: 3 }}>
            {msg.sender_name?.split(' ')[0]?.toUpperCase()}
          </div>
        )}
        <div style={{
          padding: '8px 12px',
          background: isMe ? t.accent : t.surface,
          color: isMe ? '#fff' : t.text,
          border: `1.5px solid ${isMe ? t.accent : t.border}`,
          fontSize: 12, lineHeight: '1.5', wordBreak: 'break-word',
        }}>
          <RenderContent text={msg.content} t={t} />
        </div>
        <div style={{ fontSize: 8, color: t.textMuted, marginTop: 3, letterSpacing: '0.5px', textAlign: isMe ? 'right' : 'left', display: 'flex', alignItems: 'center', gap: 6, justifyContent: isMe ? 'flex-end' : 'flex-start' }}>
          {fmtTime(msg.created_at)}
          {msg.is_pinned && <Pin size={8} style={{ color: t.accent }} />}
        </div>
      </div>

      {/* Pin action on hover */}
      {hover && onPin && !msg.id?.startsWith('opt-') && (
        <button onClick={() => onPin(msg.id)} title={msg.is_pinned ? 'Unpin' : 'Pin'} style={{
          position: 'absolute', top: -6, [isMe ? 'left' : 'right']: 0,
          background: t.card, border: `1px solid ${t.border}`, cursor: 'pointer',
          padding: '2px 5px', display: 'flex', alignItems: 'center', color: t.textMuted, fontSize: 8,
        }}>
          <Pin size={10} />
        </button>
      )}
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function MyTeam() {
  const { theme: t } = useTheme()
  const { user, token } = useAuthStore()

  const [team, setTeam] = useState([])
  const [teamLoading, setTeamLoading] = useState(true)

  const [messages, setMessages] = useState([])
  const [chatLoading, setChatLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [draft, setDraft] = useState('')
  const [wsStatus, setWsStatus] = useState('connecting')

  // New features state
  const [pinnedMsg, setPinnedMsg] = useState(null)
  const [typingUsers, setTypingUsers] = useState({})
  const [dmPartner, setDmPartner] = useState(null)
  const [dmMessages, setDmMessages] = useState([])
  const [dmDraft, setDmDraft] = useState('')
  const [dmLoading, setDmLoading] = useState(false)
  const [dmTyping, setDmTyping] = useState(null)

  const chatEndRef = useRef(null)
  const dmEndRef = useRef(null)
  const wsRef = useRef(null)
  const inputRef = useRef(null)
  const typingTimerRef = useRef(null)

  // ── Load team directory ──────────────────────────────────────────────────
  const loadTeam = useCallback(async () => {
    setTeamLoading(true)
    try {
      const res = await employeesAPI.getMyTeam()
      setTeam(res.data.team || [])
    } catch (err) {
      console.error('Failed to load team:', err)
    } finally {
      setTeamLoading(false)
    }
  }, [])

  // ── Load chat history ────────────────────────────────────────────────────
  const loadChat = useCallback(async () => {
    setChatLoading(true)
    try {
      const res = await chatAPI.getTeamChat({ limit: 50 })
      setMessages(res.data.messages || [])
    } catch (err) {
      console.error('Failed to load chat:', err)
    } finally {
      setChatLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTeam()
    loadChat()
    chatAPI.getPinned().then(r => setPinnedMsg(r.data?.pinned || null)).catch(() => {})
  }, [loadTeam, loadChat])

  // ── Auto-scroll on new messages ──────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  useEffect(() => {
    dmEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [dmMessages])

  // ── WebSocket connection ─────────────────────────────────────────────────
  useEffect(() => {
    if (!user?.id || !token) return
    const wsBase = (import.meta.env.VITE_API_URL || 'https://sentinel-ny7w.onrender.com/api/v1')
      .replace(/^http/, 'ws')
      .replace(/\/api\/v1$/, '')
    const ws = new WebSocket(`${wsBase}/ws/${user.id}`)
    wsRef.current = ws

    ws.onopen = () => setWsStatus('connected')
    ws.onclose = () => setWsStatus('disconnected')
    ws.onerror = () => setWsStatus('disconnected')
    ws.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data)
        
        // Handle Chat Messages
        if (payload.type === 'team_chat' && payload.message) {
          setMessages((prev) => {
            if (prev.find((m) => m.id === payload.message.id)) return prev
            return [...prev, payload.message]
          })
        }
        
        // Handle Real-Time Presence
        if (payload.type === 'presence') {
          setTeam(prev => prev.map(member => 
            member.id === payload.user_id 
              ? { ...member, is_online: payload.status === 'online' } 
              : member
          ))
        }

        // Handle Direct Messages
        if (payload.type === 'direct_message' && payload.message) {
          setDmMessages(prev => {
            if (prev.find(m => m.id === payload.message.id)) return prev
            return [...prev, payload.message]
          })
        }

        // Handle Typing Indicators
        if (payload.type === 'typing' && payload.user_id !== user?.id) {
          const name = payload.sender_name?.split(' ')[0] || 'Someone'
          if (payload.target === 'department') {
            setTypingUsers(prev => {
              if (prev[name]) clearTimeout(prev[name])
              const tid = setTimeout(() => setTypingUsers(p => { const n = {...p}; delete n[name]; return n }), 3000)
              return { ...prev, [name]: tid }
            })
          } else {
            setDmTyping(name)
            setTimeout(() => setDmTyping(null), 3000)
          }
        }

        // Handle Pin Updates
        if (payload.type === 'pin_update') {
          setPinnedMsg(payload.pinned || null)
        }
      } catch {}
    }

    return () => ws.close()
  }, [user?.id, token])

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = async () => {
    const content = draft.trim()
    if (!content || sending) return
    setSending(true)
    setDraft('')

    // Optimistic insert
    const optimistic = {
      id: `opt-${Date.now()}`,
      content,
      sender_id: user?.id,
      sender_name: user?.full_name,
      sender_avatar: user?.avatar_url,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimistic])

    try {
      await chatAPI.postTeamMessage({ content })
    } catch (err) {
      console.error('Failed to send:', err)
      // Remove optimistic on failure
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id))
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── Emit typing signal ─────────────────────────────────────────────────
  const emitTyping = (target) => {
    if (wsRef.current?.readyState === 1) {
      wsRef.current.send(JSON.stringify({
        type: 'typing',
        target,
        department: target === 'department' ? user?.department : undefined,
        sender_name: user?.full_name
      }))
    }
  }

  const handleGroupTyping = () => {
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current)
    typingTimerRef.current = setTimeout(() => emitTyping('department'), 300)
  }

  // ── Pin message ────────────────────────────────────────────────────────
  const handlePin = async (msgId) => {
    try {
      const res = await chatAPI.pinMessage(msgId)
      setPinnedMsg(res.data?.pinned || null)
    } catch (err) { console.error('Pin failed:', err) }
  }

  // ── Open DM drawer ─────────────────────────────────────────────────────
  const openDm = async (member) => {
    setDmPartner(member)
    setDmMessages([])
    setDmLoading(true)
    setDmDraft('')
    try {
      const res = await dmAPI.getHistory(member.id, { limit: 50 })
      setDmMessages(res.data?.messages || [])
    } catch (err) { console.error('DM load failed:', err) }
    finally { setDmLoading(false) }
  }

  // ── Send DM ────────────────────────────────────────────────────────────
  const sendDm = async () => {
    if (!dmDraft.trim() || !dmPartner) return
    const content = dmDraft.trim()
    setDmDraft('')
    const optimistic = {
      id: `opt-dm-${Date.now()}`, content,
      sender_id: user?.id, sender_name: user?.full_name,
      sender_avatar: user?.avatar_url, receiver_id: dmPartner.id,
      receiver_name: dmPartner.full_name, created_at: new Date().toISOString(),
    }
    setDmMessages(prev => [...prev, optimistic])
    try { await dmAPI.sendMessage(dmPartner.id, { content }) }
    catch { setDmMessages(prev => prev.filter(m => m.id !== optimistic.id)) }
  }

  const typingNames = Object.keys(typingUsers)
  const onlineCount = team.filter((m) => m.is_online).length

  return (
    <div style={{ fontFamily: "'DM Mono','IBM Plex Mono',monospace", color: t.text }}>

      {/* ── Page header ── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 9, color: t.textMuted, letterSpacing: '3px', marginBottom: 6 }}>
          EMPLOYEE / MY TEAM
        </div>
        <h1
          style={{
            fontSize: 22,
            fontWeight: 900,
            letterSpacing: '-1px',
            color: t.text,
            margin: 0,
          }}
        >
          {user?.department ? `${user.department} Department` : 'My Team'}
        </h1>
        <div style={{ fontSize: 10, color: t.textMuted, marginTop: 4, letterSpacing: '1px' }}>
          {team.length} COLLEAGUES · {onlineCount} ONLINE NOW
        </div>
      </div>

      {/* ── Layout: Directory + Chat ── */}
      <div
        className="myteam-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0,1fr) minmax(0,1.4fr)',
          gap: 20,
          alignItems: 'start',
        }}
      >
        {/* ── LEFT: Team Directory ── */}
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 12,
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                letterSpacing: '2px',
                color: t.textMuted,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <Users size={12} /> TEAM DIRECTORY
            </div>
            <button
              onClick={loadTeam}
              style={{
                background: 'transparent',
                border: 'none',
                color: t.textMuted,
                cursor: 'pointer',
                padding: 4,
                display: 'flex',
              }}
              title="Refresh"
            >
              <RefreshCw size={13} />
            </button>
          </div>

          {teamLoading ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
              }}
            >
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  style={{
                    height: 72,
                    background: t.card,
                    border: `1.5px solid ${t.border}`,
                    opacity: 0.5,
                    animation: 'pulse 1.4s infinite',
                  }}
                />
              ))}
            </div>
          ) : team.length === 0 ? (
            <div
              style={{
                padding: '40px 20px',
                textAlign: 'center',
                color: t.textMuted,
                fontSize: 10,
                letterSpacing: '1px',
                border: `1.5px dashed ${t.border}`,
              }}
            >
              NO TEAMMATES FOUND
              <div style={{ marginTop: 6, fontSize: 9 }}>
                You may not have a department assigned yet.
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {team.map((member) => (
                <MemberCard key={member.id} member={member} t={t} onDm={openDm} />
              ))}
            </div>
          )}
        </div>

        {/* ── RIGHT: Group Chat ── */}
        <div
          style={{
            border: `1.5px solid ${t.border}`,
            background: t.card,
            display: 'flex',
            flexDirection: 'column',
            height: 'calc(100vh - 200px)',
            minHeight: 400,
            maxHeight: 680,
          }}
        >
          {/* Chat header */}
          <div
            style={{
              padding: '12px 16px',
              borderBottom: `1.5px solid ${t.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexShrink: 0,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                fontSize: 9,
                fontWeight: 700,
                letterSpacing: '2px',
                color: t.textMuted,
              }}
            >
              <MessageSquare size={12} />
              {user?.department?.toUpperCase() || 'TEAM'} CHAT
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                fontSize: 8,
                letterSpacing: '1px',
                color: wsStatus === 'connected' ? '#22c55e' : wsStatus === 'connecting' ? '#f59e0b' : '#ef4444',
              }}
            >
              {wsStatus === 'connected' ? (
                <Wifi size={11} />
              ) : (
                <WifiOff size={11} />
              )}
              {wsStatus.toUpperCase()}
            </div>
          </div>

          {/* Pinned message banner */}
          {pinnedMsg && (
            <div style={{
              padding: '8px 14px', borderBottom: `1.5px solid ${t.border}`,
              background: t.accent + '11', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0,
            }}>
              <Pin size={10} style={{ color: t.accent, flexShrink: 0 }} />
              <div style={{ fontSize: 10, color: t.text, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                <span style={{ color: t.textMuted, marginRight: 6 }}>{pinnedMsg.sender_name?.split(' ')[0]}:</span>
                {pinnedMsg.content}
              </div>
              <button onClick={() => handlePin(pinnedMsg.id)} style={{ background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', padding: 2, display: 'flex' }}>
                <X size={12} />
              </button>
            </div>
          )}

          {/* Messages area */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {chatLoading ? (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: t.textMuted,
                  fontSize: 10,
                  letterSpacing: '2px',
                }}
              >
                LOADING CHAT...
              </div>
            ) : messages.length === 0 ? (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column',
                  gap: 8,
                  color: t.textMuted,
                }}
              >
                <MessageSquare size={28} strokeWidth={1} />
                <div style={{ fontSize: 9, letterSpacing: '2px' }}>NO MESSAGES YET</div>
                <div style={{ fontSize: 9, letterSpacing: '1px' }}>
                  Be the first to say something!
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <ChatBubble
                    key={msg.id}
                    msg={msg}
                    isMe={msg.sender_id === user?.id}
                    t={t}
                    onPin={handlePin}
                  />
                ))}
                <div ref={chatEndRef} />
              </>
            )}
          </div>

          {/* Typing indicator */}
          {typingNames.length > 0 && (
            <div style={{ padding: '4px 16px', fontSize: 9, color: t.accent, letterSpacing: '0.5px', flexShrink: 0 }}>
              {typingNames.join(', ')} {typingNames.length === 1 ? 'is' : 'are'} typing
              <span style={{ animation: 'blink 1s infinite' }}>...</span>
            </div>
          )}

          {/* Input area */}
          <div
            style={{
              padding: '12px 14px',
              borderTop: `1.5px solid ${t.border}`,
              display: 'flex',
              gap: 10,
              alignItems: 'flex-end',
              flexShrink: 0,
            }}
          >
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              onInput={handleGroupTyping}
              placeholder="Type a message… (Enter to send)"
              rows={1}
              style={{
                flex: 1,
                background: t.surface,
                border: `1.5px solid ${t.border}`,
                color: t.text,
                padding: '9px 12px',
                fontSize: 12,
                fontFamily: 'inherit',
                outline: 'none',
                resize: 'none',
                lineHeight: '1.4',
                maxHeight: 100,
                overflow: 'auto',
              }}
              onFocus={(e) => (e.target.style.borderColor = t.accent)}
              onBlur={(e) => (e.target.style.borderColor = t.border)}
            />
            <button
              onClick={sendMessage}
              disabled={!draft.trim() || sending}
              style={{
                width: 38,
                height: 38,
                flexShrink: 0,
                background: draft.trim() && !sending ? t.accent : t.surface,
                border: `1.5px solid ${draft.trim() && !sending ? t.accent : t.border}`,
                color: draft.trim() && !sending ? '#fff' : t.textMuted,
                cursor: draft.trim() && !sending ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.15s',
              }}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* ── DM Drawer Overlay ── */}
      {dmPartner && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', justifyContent: 'flex-end' }}>
          <div onClick={() => setDmPartner(null)} style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(2px)' }} />
          <div style={{
            position: 'relative', width: 400, maxWidth: '90vw', height: '100%',
            background: t.bg, borderLeft: `2px solid ${t.border}`,
            display: 'flex', flexDirection: 'column',
          }}>
            {/* DM Header */}
            <div style={{ padding: '14px 16px', borderBottom: `1.5px solid ${t.border}`, display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
              <button onClick={() => setDmPartner(null)} style={{ background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', display: 'flex', padding: 2 }}>
                <ArrowLeft size={16} />
              </button>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: avatarColor(dmPartner.full_name), overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: '#fff' }}>
                {dmPartner.avatar_url ? <img src={dmPartner.avatar_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : initials(dmPartner.full_name)}
              </div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: t.text }}>{dmPartner.full_name}</div>
                <div style={{ fontSize: 8, color: dmPartner.is_online ? '#22c55e' : t.textMuted, letterSpacing: '1px' }}>
                  {dmPartner.is_online ? 'ONLINE' : 'OFFLINE'}
                </div>
              </div>
            </div>

            {/* DM Messages */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column' }}>
              {dmLoading ? (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: t.textMuted, fontSize: 10, letterSpacing: '2px' }}>LOADING...</div>
              ) : dmMessages.length === 0 ? (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 6, color: t.textMuted }}>
                  <Mail size={24} strokeWidth={1} />
                  <div style={{ fontSize: 9, letterSpacing: '1px' }}>NO MESSAGES YET</div>
                </div>
              ) : (
                <>
                  {dmMessages.map(msg => (
                    <ChatBubble key={msg.id} msg={msg} isMe={msg.sender_id === user?.id} t={t} />
                  ))}
                  <div ref={dmEndRef} />
                </>
              )}
            </div>

            {/* DM Typing */}
            {dmTyping && (
              <div style={{ padding: '4px 16px', fontSize: 9, color: t.accent, letterSpacing: '0.5px' }}>
                {dmTyping} is typing<span style={{ animation: 'blink 1s infinite' }}>...</span>
              </div>
            )}

            {/* DM Input */}
            <div style={{ padding: '12px 14px', borderTop: `1.5px solid ${t.border}`, display: 'flex', gap: 10, alignItems: 'flex-end', flexShrink: 0 }}>
              <textarea
                value={dmDraft}
                onChange={e => setDmDraft(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendDm() } }}
                onInput={() => emitTyping(dmPartner.id)}
                placeholder={`Message ${dmPartner.full_name?.split(' ')[0]}…`}
                rows={1}
                style={{
                  flex: 1, background: t.surface, border: `1.5px solid ${t.border}`,
                  color: t.text, padding: '9px 12px', fontSize: 12, fontFamily: 'inherit',
                  outline: 'none', resize: 'none', lineHeight: '1.4', maxHeight: 100, overflow: 'auto',
                }}
                onFocus={e => e.target.style.borderColor = t.accent}
                onBlur={e => e.target.style.borderColor = t.border}
              />
              <button onClick={sendDm} disabled={!dmDraft.trim()} style={{
                width: 38, height: 38, flexShrink: 0,
                background: dmDraft.trim() ? t.accent : t.surface,
                border: `1.5px solid ${dmDraft.trim() ? t.accent : t.border}`,
                color: dmDraft.trim() ? '#fff' : t.textMuted,
                cursor: dmDraft.trim() ? 'pointer' : 'not-allowed',
                display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s',
              }}>
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Responsive + animations */}
      <style>{`
        @media (max-width: 700px) {
          .myteam-grid {
            grid-template-columns: 1fr !important;
            gap: 16px !important;
          }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 0.2; }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.2; }
        }
      `}</style>
    </div>
  )
}
