import { useEffect, useState } from 'react'
import { workRulesAPI } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { Settings2, Save, Plus, Trash2, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const DEPTS       = ['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations']
const SENSITIV    = ['low', 'medium', 'high']
const EMPTY_RULE  = { department: 'Engineering', work_minutes_per_hour: 50, break_minutes_per_hour: 10, lunch_duration_minutes: 30, daily_work_target_minutes: 400, detection_sensitivity: 'medium' }

function validateRule(r) {
  const errs = {}
  if (r.work_minutes_per_hour  < 1 || r.work_minutes_per_hour  > 60) errs.work  = 'Must be 1–60'
  if (r.break_minutes_per_hour < 0 || r.break_minutes_per_hour > 60) errs.brk   = 'Must be 0–60'
  if (r.lunch_duration_minutes < 0 || r.lunch_duration_minutes > 120) errs.lunch = 'Must be 0–120'
  if (r.daily_work_target_minutes < 60 || r.daily_work_target_minutes > 600) errs.target = 'Must be 60–600'
  if ((r.work_minutes_per_hour + r.break_minutes_per_hour) > 60) errs.sum = 'Work + Break cannot exceed 60 min/hr'
  return errs
}

function RuleFields({ value, onChange, errors }) {
  const fields = [
    { key: 'work_minutes_per_hour',     label: 'Work Min/Hr',  errKey: 'work' },
    { key: 'break_minutes_per_hour',    label: 'Break Min/Hr', errKey: 'brk'  },
    { key: 'lunch_duration_minutes',    label: 'Lunch (min)',  errKey: 'lunch' },
    { key: 'daily_work_target_minutes', label: 'Daily Target', errKey: 'target' },
  ]
  return (
    <div className="space-y-3">
      {errors.sum && (
        <div className="flex items-center gap-2 text-xs font-mono text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
          <AlertCircle size={13} /> {errors.sum}
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {fields.map(f => (
          <div key={f.key}>
            <p className="label mb-1">{f.label}</p>
            <input type="number" value={value[f.key]}
              onChange={e => onChange({ ...value, [f.key]: Number(e.target.value) })}
              className={`input-field ${errors[f.errKey] ? 'border-red-500/50' : ''}`}
            />
            {errors[f.errKey] && <p className="text-red-400 text-[10px] font-mono mt-1">{errors[f.errKey]}</p>}
          </div>
        ))}
      </div>
      <div>
        <p className="label mb-1">Detection Sensitivity</p>
        <div className="flex gap-2">
          {SENSITIV.map(s => (
            <button key={s} type="button"
              onClick={() => onChange({ ...value, detection_sensitivity: s })}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all capitalize
                ${value.detection_sensitivity === s ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20' : 'text-sentinel-muted border-sentinel-border hover:text-sentinel-text'}`}>
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function Settings() {
  const { user }       = useAuthStore()
  const [rules,    setRules]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [editing,  setEditing]  = useState(null)   // rule id being edited
  const [editVals, setEditVals] = useState({})      // edited values
  const [editErrs, setEditErrs] = useState({})
  const [saving,   setSaving]   = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [showNew,  setShowNew]  = useState(false)
  const [newRule,  setNewRule]  = useState(EMPTY_RULE)
  const [newErrs,  setNewErrs]  = useState({})

  useEffect(() => {
    workRulesAPI.getAll()
      .then(r => setRules(r.data?.rules || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const startEdit = (rule) => {
    setEditing(rule.id)
    setEditVals({ ...rule })
    setEditErrs({})
  }

  const cancelEdit = () => { setEditing(null); setEditVals({}); setEditErrs({}) }

  const saveEdit = async (ruleId) => {
    const errs = validateRule(editVals)
    if (Object.keys(errs).length) { setEditErrs(errs); return }
    setSaving(true)
    try {
      const { id, created_at, updated_at, ...updates } = editVals
      await workRulesAPI.update(ruleId, updates)
      setRules(prev => prev.map(r => r.id === ruleId ? { ...r, ...editVals } : r))
      cancelEdit()
      toast.success('Rule updated')
    } catch { toast.error('Failed to save') }
    finally { setSaving(false) }
  }

  const deleteRule = async (rule) => {
    if (!window.confirm(`Delete rule for ${rule.department || 'Global'}? This cannot be undone.`)) return
    setDeleting(rule.id)
    try {
      await workRulesAPI.remove(rule.id)
      setRules(prev => prev.filter(r => r.id !== rule.id))
      toast.success('Rule deleted')
    } catch { toast.error('Failed to delete') }
    finally { setDeleting(null) }
  }

  const createRule = async () => {
    const errs = validateRule(newRule)
    if (Object.keys(errs).length) { setNewErrs(errs); return }
    setSaving(true)
    try {
      const res = await workRulesAPI.create(newRule)
      setRules(prev => [...prev, res.data.rule])
      setShowNew(false)
      setNewRule(EMPTY_RULE)
      setNewErrs({})
      toast.success('Rule created')
    } catch { toast.error('Failed to create rule') }
    finally { setSaving(false) }
  }

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Settings</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">Manage work rules and detection configuration</p>
      </div>
      <div className="glow-line" />

      {/* Admin profile */}
      <div className="card p-5 animate-fade-in stagger-1">
        <h3 className="section-title mb-4">Admin Profile</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { label: 'Full Name', value: user?.full_name },
            { label: 'Email',     value: user?.email },
            { label: 'Role',      value: user?.role?.replace('_', ' ').toUpperCase() },
          ].map(f => (
            <div key={f.label}>
              <p className="label mb-1">{f.label}</p>
              <p className="font-mono text-sm text-sentinel-text">{f.value || '—'}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Work rules */}
      <div className="animate-fade-in stagger-2">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="section-title">Work Rules</h3>
            <p className="text-xs font-mono text-sentinel-muted mt-0.5">Configure work/break minutes and detection sensitivity per department</p>
          </div>
          <button onClick={() => { setShowNew(s => !s); setNewErrs({}) }}
            className="btn-ghost flex items-center gap-2 text-xs">
            <Plus size={13} /> New Rule
          </button>
        </div>

        {/* New rule form */}
        {showNew && (
          <div className="card p-5 mb-4 border-cyan-400/15 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <p className="label">New Work Rule</p>
              <div>
                <p className="label mb-1">Department</p>
                <select value={newRule.department}
                  onChange={e => setNewRule(p => ({ ...p, department: e.target.value }))}
                  className="input-field w-auto">
                  {DEPTS.map(d => <option key={d}>{d}</option>)}
                </select>
              </div>
            </div>
            <RuleFields value={newRule} onChange={setNewRule} errors={newErrs} />
            <div className="flex gap-3 mt-4">
              <button onClick={() => { setShowNew(false); setNewErrs({}) }} className="btn-ghost">Cancel</button>
              <button onClick={createRule} disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50">
                <Plus size={13} /> {saving ? 'Creating…' : 'Create Rule'}
              </button>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {loading ? (
            Array(3).fill(0).map((_, i) => (
              <div key={i} className="card p-5"><div className="h-4 bg-navy-700 rounded animate-pulse" /></div>
            ))
          ) : rules.length === 0 ? (
            <div className="card p-8 text-center">
              <Settings2 size={24} className="text-sentinel-muted mx-auto mb-2" />
              <p className="text-sentinel-muted text-sm font-mono">No rules configured</p>
            </div>
          ) : rules.map(rule => (
            <div key={rule.id} className="card p-5">
              {/* Rule header */}
              <div className="flex items-start justify-between mb-3 gap-3 flex-wrap">
                <div>
                  <p className="font-mono font-semibold text-sentinel-text">{rule.department || 'Global'}</p>
                  <p className="text-xs font-mono text-sentinel-muted mt-0.5">
                    Sensitivity: <span className={
                      rule.detection_sensitivity === 'high'   ? 'text-red-400' :
                      rule.detection_sensitivity === 'low'    ? 'text-emerald-400' : 'text-amber-400'
                    }>{rule.detection_sensitivity}</span>
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => editing === rule.id ? cancelEdit() : startEdit(rule)}
                    className="btn-ghost text-xs"
                  >
                    {editing === rule.id ? 'Cancel' : 'Edit'}
                  </button>
                  <button
                    onClick={() => deleteRule(rule)}
                    disabled={deleting === rule.id}
                    className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1.5 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-400/10 transition-all disabled:opacity-50"
                  >
                    <Trash2 size={12} />
                    {deleting === rule.id ? '…' : 'Delete'}
                  </button>
                </div>
              </div>

              {editing === rule.id ? (
                <div className="space-y-3">
                  <RuleFields value={editVals} onChange={setEditVals} errors={editErrs} />
                  <button onClick={() => saveEdit(rule.id)} disabled={saving}
                    className="btn-primary flex items-center gap-2 disabled:opacity-50">
                    <Save size={13} /> {saving ? 'Saving…' : 'Save Changes'}
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Work/Hour',    value: `${rule.work_minutes_per_hour}min` },
                    { label: 'Break/Hour',   value: `${rule.break_minutes_per_hour}min` },
                    { label: 'Lunch',        value: `${rule.lunch_duration_minutes}min` },
                    { label: 'Daily Target', value: `${rule.daily_work_target_minutes}min` },
                  ].map(f => (
                    <div key={f.label}>
                      <p className="label mb-0.5">{f.label}</p>
                      <p className="font-mono text-sm text-sentinel-text">{f.value}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}