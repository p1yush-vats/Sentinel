import { useEffect, useState } from 'react'
import { tasksAPI, employeesAPI } from '../services/api'
import { CheckSquare, Plus, Trash2, Clock, AlertCircle, ChevronDown, X } from 'lucide-react'
import toast from 'react-hot-toast'

const PRIORITY_STYLES = {
  low:    'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  medium: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
  high:   'text-orange-400 bg-orange-400/10 border-orange-400/20',
  urgent: 'text-red-400 bg-red-400/10 border-red-400/20',
}

const STATUS_STYLES = {
  pending:     'text-slate-400 bg-slate-400/10 border-slate-400/20',
  in_progress: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  completed:   'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
}

function AssignModal({ employees, onClose, onCreate }) {
  const [form, setForm] = useState({ title: '', description: '', assigned_to: '', priority: 'medium', due_date: '' })
  const [saving, setSaving] = useState(false)

  const submit = async () => {
    if (!form.title.trim() || !form.assigned_to) { toast.error('Title and employee are required'); return }
    setSaving(true)
    try {
      await onCreate({ ...form, due_date: form.due_date ? new Date(form.due_date).toISOString() : null })
      onClose()
    } catch { toast.error('Failed to create task') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-navy-800 border border-sentinel-border rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-fade-in">
        <div className="p-4 border-b border-sentinel-border bg-navy-900/50 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-violet-400" />
            <h3 className="font-display font-semibold text-sentinel-text">Assign New Task</h3>
          </div>
          <button onClick={onClose} className="text-sentinel-muted hover:text-white transition-colors"><X className="w-5 h-5" /></button>
        </div>

        <div className="p-5 space-y-4">
          {/* Title */}
          <div>
            <p className="label mb-1">Task Title *</p>
            <input
              className="input-field w-full"
              placeholder="e.g. Submit monthly timesheet"
              value={form.title}
              onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
            />
          </div>

          {/* Description */}
          <div>
            <p className="label mb-1">Description</p>
            <textarea
              className="input-field w-full resize-none h-20"
              placeholder="Optional details..."
              value={form.description}
              onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
            />
          </div>

          {/* Employee */}
          <div>
            <p className="label mb-1">Assign To *</p>
            <select
              className="input-field w-full"
              value={form.assigned_to}
              onChange={e => setForm(p => ({ ...p, assigned_to: e.target.value }))}
            >
              <option value="">— Select employee —</option>
              {employees.filter(e => e.role !== 'admin').map(e => (
                <option key={e.id} value={e.id}>{e.full_name} ({e.department || 'No dept'})</option>
              ))}
            </select>
          </div>

          {/* Priority + Due Date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="label mb-1">Priority</p>
              <select className="input-field w-full" value={form.priority} onChange={e => setForm(p => ({ ...p, priority: e.target.value }))}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <p className="label mb-1">Due Date</p>
              <input type="date" className="input-field w-full" value={form.due_date} onChange={e => setForm(p => ({ ...p, due_date: e.target.value }))} />
            </div>
          </div>
        </div>

        <div className="p-4 bg-navy-900/50 border-t border-sentinel-border flex justify-end gap-3">
          <button onClick={onClose} className="btn-ghost text-sm">Cancel</button>
          <button onClick={submit} disabled={saving} className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50">
            <Plus size={14} /> {saving ? 'Creating…' : 'Assign Task'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Tasks() {
  const [tasks, setTasks]         = useState([])
  const [employees, setEmployees] = useState([])
  const [loading, setLoading]     = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [filterEmp, setFilterEmp] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  const load = () => {
    const params = {}
    if (filterEmp)    params.assigned_to = filterEmp
    if (filterStatus) params.status = filterStatus
    tasksAPI.getAll(params)
      .then(r => setTasks(r.data?.tasks || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    employeesAPI.getAll().then(r => setEmployees(r.data?.employees || [])).catch(() => {})
  }, [])

  useEffect(() => { load() }, [filterEmp, filterStatus])

  const handleCreate = async (data) => {
    const res = await tasksAPI.create(data)
    setTasks(prev => [res.data.task, ...prev])
    toast.success('Task assigned!')
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this task?')) return
    try {
      await tasksAPI.remove(id)
      setTasks(prev => prev.filter(t => t.id !== id))
      toast.success('Task deleted')
    } catch { toast.error('Failed to delete') }
  }

  const getName = (id) => employees.find(e => e.id === id)?.full_name || id?.slice(0, 8) + '…'

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Tasks</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">Assign and track employee tasks</p>
      </div>
      <div className="glow-line" />

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 animate-fade-in stagger-1">
        <select className="input-field w-auto text-sm" value={filterEmp} onChange={e => setFilterEmp(e.target.value)}>
          <option value="">All employees</option>
          {employees.filter(e => e.role !== 'admin').map(e => <option key={e.id} value={e.id}>{e.full_name}</option>)}
        </select>
        <select className="input-field w-auto text-sm" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
        <div className="ml-auto">
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus size={14} /> Assign Task
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="card animate-fade-in stagger-2 overflow-hidden">
        {loading ? (
          <div className="p-8 space-y-3">
            {Array(4).fill(0).map((_, i) => <div key={i} className="h-12 bg-navy-700 rounded animate-pulse" />)}
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-12 text-center">
            <CheckSquare size={28} className="text-sentinel-muted mx-auto mb-3" />
            <p className="text-sentinel-muted text-sm font-mono">No tasks found</p>
            <p className="text-sentinel-muted text-xs font-mono mt-1">Assign your first task using the button above</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-sentinel-border">
                  {['Task', 'Assigned To', 'Priority', 'Status', 'Due Date', ''].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-mono text-sentinel-muted uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-sentinel-border/50">
                {tasks.map(task => (
                  <tr key={task.id} className="hover:bg-navy-800/40 transition-colors group">
                    <td className="px-4 py-3">
                      <p className="text-sm font-mono text-sentinel-text font-medium">{task.title}</p>
                      {task.description && <p className="text-xs font-mono text-sentinel-muted mt-0.5 max-w-xs truncate">{task.description}</p>}
                      {task.completion_note && task.status === 'completed' && (
                        <p className="text-xs font-mono text-emerald-400 mt-0.5">Note: {task.completion_note}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-sentinel-text">{getName(task.assigned_to)}</td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] font-mono font-bold px-2 py-1 rounded-md border uppercase ${PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium}`}>
                        {task.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] font-mono font-bold px-2 py-1 rounded-md border ${STATUS_STYLES[task.status] || STATUS_STYLES.pending}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-sentinel-muted">
                      {task.due_date ? new Date(task.due_date).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleDelete(task.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-400/10"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && <AssignModal employees={employees} onClose={() => setShowModal(false)} onCreate={handleCreate} />}
    </div>
  )
}
