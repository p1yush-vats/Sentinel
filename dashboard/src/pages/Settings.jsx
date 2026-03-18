import { useEffect, useState } from 'react'
import { workRulesAPI } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { Settings2, Save, Plus } from 'lucide-react'
import toast from 'react-hot-toast'

const DEPTS = ['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations']

export default function Settings() {
  const { user }          = useAuthStore()
  const [rules,    setRules]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [editing,  setEditing]  = useState(null)
  const [saving,   setSaving]   = useState(false)
  const [showNew,  setShowNew]  = useState(false)
  const [newRule,  setNewRule]  = useState({ department: 'Engineering', work_minutes_per_hour: 50, break_minutes_per_hour: 10, lunch_duration_minutes: 30, daily_work_target_minutes: 400, detection_sensitivity: 'medium' })

  useEffect(() => {
    workRulesAPI.getAll()
      .then(r => setRules(r.data?.rules || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const save = async (rule) => {
    setSaving(true)
    try {
      const updates = { ...editing }
      delete updates.id
      delete updates.created_at
      delete updates.updated_at
      await workRulesAPI.update(rule.id, updates)
      setRules(prev => prev.map(r => r.id === rule.id ? { ...r, ...editing } : r))
      setEditing(null)
      toast.success('Rule updated')
    } catch { toast.error('Failed to save') }
    finally { setSaving(false) }
  }

  const create = async () => {
    setSaving(true)
    try {
      const res = await workRulesAPI.create(newRule)
      setRules(prev => [...prev, res.data.rule])
      setShowNew(false)
      toast.success('Rule created')
    } catch { toast.error('Failed to create rule') }
    finally { setSaving(false) }
  }

  const SENSITIVITIES = ['low', 'medium', 'high']

  return (
    <div className="space-y-6">
      <div className="animate-fade-in">
        <h1 className="font-display font-bold text-2xl text-sentinel-text">Settings</h1>
        <p className="text-sentinel-muted text-sm font-mono mt-1">Manage work rules and detection sensitivity</p>
      </div>

      <div className="glow-line" />

      {/* Admin info */}
      <div className="card p-5 animate-fade-in stagger-1">
        <h3 className="section-title mb-4">Admin Profile</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { label: 'Full Name',   value: user?.full_name },
            { label: 'Email',       value: user?.email },
            { label: 'Role',        value: user?.role?.replace('_', ' ').toUpperCase() },
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
          <h3 className="section-title">Work Rules</h3>
          <button onClick={() => setShowNew(!showNew)} className="btn-ghost flex items-center gap-2 text-xs">
            <Plus size={13} /> New Rule
          </button>
        </div>

        {showNew && (
          <div className="card p-5 mb-4 border-cyan-400/15 animate-fade-in">
            <p className="label mb-4">New Work Rule</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
              <div>
                <p className="label mb-1">Department</p>
                <select value={newRule.department} onChange={e => setNewRule(p => ({ ...p, department: e.target.value }))} className="input-field">
                  {DEPTS.map(d => <option key={d}>{d}</option>)}
                </select>
              </div>
              {[
                { key: 'work_minutes_per_hour',     label: 'Work Min/Hour' },
                { key: 'break_minutes_per_hour',    label: 'Break Min/Hour' },
                { key: 'lunch_duration_minutes',    label: 'Lunch Duration' },
                { key: 'daily_work_target_minutes', label: 'Daily Target (min)' },
              ].map(f => (
                <div key={f.key}>
                  <p className="label mb-1">{f.label}</p>
                  <input type="number" value={newRule[f.key]} onChange={e => setNewRule(p => ({ ...p, [f.key]: Number(e.target.value) }))} className="input-field" />
                </div>
              ))}
              <div>
                <p className="label mb-1">Sensitivity</p>
                <select value={newRule.detection_sensitivity} onChange={e => setNewRule(p => ({ ...p, detection_sensitivity: e.target.value }))} className="input-field">
                  {SENSITIVITIES.map(s => <option key={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <button onClick={create} disabled={saving} className="btn-primary disabled:opacity-50">
              {saving ? 'Creating...' : 'Create Rule'}
            </button>
          </div>
        )}

        <div className="space-y-3">
          {loading ? (
            Array(3).fill(0).map((_, i) => <div key={i} className="card p-5"><div className="h-4 bg-navy-700 rounded animate-pulse" /></div>)
          ) : rules.length === 0 ? (
            <div className="card p-8 text-center">
              <Settings2 size={24} className="text-sentinel-muted mx-auto mb-2" />
              <p className="text-sentinel-muted text-sm font-mono">No rules configured</p>
            </div>
          ) : rules.map(rule => (
            <div key={rule.id} className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="font-mono font-semibold text-sentinel-text">{rule.department || 'Global'}</p>
                  <p className="text-xs font-mono text-sentinel-muted mt-0.5">
                    Sensitivity: <span className={rule.detection_sensitivity === 'high' ? 'text-red-400' : rule.detection_sensitivity === 'low' ? 'text-emerald-400' : 'text-amber-400'}>{rule.detection_sensitivity}</span>
                  </p>
                </div>
                <button
                  onClick={() => setEditing(editing?.id === rule.id ? null : { ...rule })}
                  className="btn-ghost text-xs"
                >
                  {editing?.id === rule.id ? 'Cancel' : 'Edit'}
                </button>
              </div>

              {editing?.id === rule.id ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { key: 'work_minutes_per_hour',     label: 'Work Min/Hr' },
                      { key: 'break_minutes_per_hour',    label: 'Break Min/Hr' },
                      { key: 'lunch_duration_minutes',    label: 'Lunch (min)' },
                      { key: 'daily_work_target_minutes', label: 'Daily Target' },
                    ].map(f => (
                      <div key={f.key}>
                        <p className="label mb-1">{f.label}</p>
                        <input type="number" value={editing[f.key]} onChange={e => setEditing(p => ({ ...p, [f.key]: Number(e.target.value) }))} className="input-field" />
                      </div>
                    ))}
                  </div>
                  <div>
                    <p className="label mb-1">Detection Sensitivity</p>
                    <div className="flex gap-2">
                      {SENSITIVITIES.map(s => (
                        <button key={s} onClick={() => setEditing(p => ({ ...p, detection_sensitivity: s }))}
                          className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all capitalize
                            ${editing.detection_sensitivity === s ? 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20' : 'text-sentinel-muted border-sentinel-border'}`}>
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                  <button onClick={() => save(rule)} disabled={saving} className="btn-primary flex items-center gap-2 disabled:opacity-50">
                    <Save size={13} /> {saving ? 'Saving...' : 'Save Changes'}
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
