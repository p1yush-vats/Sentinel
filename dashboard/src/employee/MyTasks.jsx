import { useEffect, useState } from 'react'
import { tasksAPI } from '../services/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

const PRIORITY_COLORS = {
  low:    { bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.25)', text: '#10B981', dot: '#10B981' },
  medium: { bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.25)', text: '#F59E0B', dot: '#F59E0B' },
  high:   { bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.25)', text: '#F97316', dot: '#F97316' },
  urgent: { bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.25)',  text: '#EF4444', dot: '#EF4444' },
}

const STATUS_LABELS = { pending: 'Pending', in_progress: 'In Progress', completed: 'Completed' }

function NoteModal({ task, onClose, onConfirm }) {
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 999, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}>
      <div style={{ background: '#0D1526', border: '1px solid #1E2D45', borderRadius: 14, width: '100%', maxWidth: 400, padding: 24, boxShadow: '0 25px 60px rgba(0,0,0,0.6)' }}>
        <h3 style={{ color: '#E2E8F0', fontFamily: 'inherit', fontSize: 15, fontWeight: 700, marginBottom: 8 }}>Mark as Complete</h3>
        <p style={{ color: '#94A3B8', fontSize: 12, marginBottom: 16, fontFamily: 'inherit' }}>{task.title}</p>
        <textarea
          placeholder="Add a completion note (optional)…"
          value={note}
          onChange={e => setNote(e.target.value)}
          style={{ width: '100%', background: '#111C2E', border: '1px solid #1E2D45', borderRadius: 8, padding: '10px 12px', color: '#E2E8F0', fontSize: 12, fontFamily: 'inherit', resize: 'none', height: 80, outline: 'none', boxSizing: 'border-box' }}
        />
        <div style={{ display: 'flex', gap: 10, marginTop: 16, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '8px 16px', background: 'transparent', border: '1px solid #1E2D45', color: '#94A3B8', borderRadius: 8, cursor: 'pointer', fontSize: 12, fontFamily: 'inherit' }}>Cancel</button>
          <button
            disabled={saving}
            onClick={async () => { setSaving(true); await onConfirm(note); setSaving(false) }}
            style={{ padding: '8px 20px', background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.3)', color: '#10B981', borderRadius: 8, cursor: 'pointer', fontSize: 12, fontWeight: 700, fontFamily: 'inherit' }}
          >
            {saving ? 'Saving…' : '✓ Confirm Done'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function MyTasks() {
  const { theme: t } = (() => {
    try { return require('./ThemeContext').useTheme() } catch { return { theme: null } }
  })()

  const [tasks, setTasks]         = useState([])
  const [loading, setLoading]     = useState(true)
  const [filter, setFilter]       = useState('all')   // all | pending | in_progress | completed
  const [noteTask, setNoteTask]   = useState(null)

  const load = () => {
    const params = filter !== 'all' ? { status: filter } : {}
    tasksAPI.getMy(params)
      .then(r => setTasks(r.data?.tasks || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filter])

  const updateStatus = async (taskId, status, note = '') => {
    try {
      const res = await tasksAPI.updateStatus(taskId, { status, completion_note: note })
      setTasks(prev => prev.map(t => t.id === taskId ? res.data.task : t))
      toast.success(status === 'completed' ? 'Task marked complete! 🎉' : 'Task updated')
      setNoteTask(null)
    } catch { toast.error('Failed to update task') }
  }

  const textColor   = '#E2E8F0'
  const mutedColor  = '#94A3B8'
  const bgColor     = '#0B1120'
  const surfaceColor = '#0D1526'
  const cardColor   = '#111C2E'
  const borderColor = '#1E2D45'

  const FILTERS = [
    { key: 'all', label: 'All' },
    { key: 'pending', label: 'Pending' },
    { key: 'in_progress', label: 'In Progress' },
    { key: 'completed', label: 'Completed' },
  ]

  return (
    <div style={{ fontFamily: "'DM Mono','IBM Plex Mono',monospace" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 22, fontWeight: 900, color: textColor, letterSpacing: '-0.5px', marginBottom: 4 }}>MY TASKS</div>
        <div style={{ fontSize: 11, color: mutedColor, letterSpacing: '2px' }}>ASSIGNED BY YOUR MANAGER</div>
      </div>

      {/* Filter pills */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            style={{
              padding: '6px 14px',
              fontSize: 10, letterSpacing: '1.5px', fontWeight: 700,
              background: filter === f.key ? '#3B82F6' : 'transparent',
              border: `2px solid ${filter === f.key ? '#3B82F6' : borderColor}`,
              color: filter === f.key ? '#fff' : mutedColor,
              borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit',
              transition: 'all 0.15s',
            }}
          >{f.label.toUpperCase()}</button>
        ))}
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[1,2,3].map(i => <div key={i} style={{ height: 90, background: cardColor, borderRadius: 12, animation: 'pulse 1.5s ease-in-out infinite' }} />)}
        </div>
      ) : tasks.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: mutedColor }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>✓</div>
          <div style={{ fontSize: 13, letterSpacing: '2px', fontWeight: 700 }}>NO TASKS</div>
          <div style={{ fontSize: 11, marginTop: 6, opacity: 0.7 }}>You're all caught up</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {tasks.map(task => {
            const pc = PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.medium
            const isCompleted = task.status === 'completed'
            const isInProgress = task.status === 'in_progress'
            return (
              <div
                key={task.id}
                style={{
                  background: isCompleted ? 'rgba(16,185,129,0.04)' : cardColor,
                  border: `1px solid ${isCompleted ? 'rgba(16,185,129,0.2)' : borderColor}`,
                  borderRadius: 12,
                  padding: '16px 20px',
                  display: 'flex', alignItems: 'flex-start', gap: 16,
                  transition: 'all 0.2s',
                  opacity: isCompleted ? 0.75 : 1,
                }}
              >
                {/* Priority dot */}
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: pc.dot, marginTop: 5, flexShrink: 0 }} />

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 4 }}>
                    <span style={{
                      fontSize: 13, fontWeight: 700, color: isCompleted ? '#10B981' : textColor,
                      textDecoration: isCompleted ? 'line-through' : 'none',
                    }}>{task.title}</span>
                    <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 4, background: pc.bg, border: `1px solid ${pc.border}`, color: pc.text, letterSpacing: '1px' }}>
                      {task.priority.toUpperCase()}
                    </span>
                  </div>

                  {task.description && (
                    <div style={{ fontSize: 11, color: mutedColor, marginBottom: 8, lineHeight: 1.5 }}>{task.description}</div>
                  )}

                  <div style={{ display: 'flex', gap: 16, fontSize: 10, color: mutedColor, flexWrap: 'wrap' }}>
                    <span>STATUS: <span style={{ color: isCompleted ? '#10B981' : isInProgress ? '#60A5FA' : mutedColor, fontWeight: 700 }}>{STATUS_LABELS[task.status]}</span></span>
                    {task.due_date && <span>DUE: {new Date(task.due_date).toLocaleDateString('en-IN', { day:'numeric', month:'short' })}</span>}
                    {task.completed_at && <span>DONE: {new Date(task.completed_at).toLocaleDateString('en-IN')}</span>}
                    {task.completion_note && <span style={{ color: '#10B981' }}>Note: "{task.completion_note}"</span>}
                  </div>
                </div>

                {/* Action buttons */}
                {!isCompleted && (
                  <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                    {!isInProgress && (
                      <button
                        onClick={() => updateStatus(task.id, 'in_progress')}
                        style={{
                          padding: '6px 12px', fontSize: 10, fontWeight: 700, letterSpacing: '1px',
                          background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.3)',
                          color: '#60A5FA', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit',
                        }}
                      >START</button>
                    )}
                    <button
                      onClick={() => setNoteTask(task)}
                      style={{
                        padding: '6px 12px', fontSize: 10, fontWeight: 700, letterSpacing: '1px',
                        background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)',
                        color: '#10B981', borderRadius: 6, cursor: 'pointer', fontFamily: 'inherit',
                      }}
                    >DONE ✓</button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {noteTask && (
        <NoteModal
          task={noteTask}
          onClose={() => setNoteTask(null)}
          onConfirm={(note) => updateStatus(noteTask.id, 'completed', note)}
        />
      )}
    </div>
  )
}
