import { useEffect, useState, useRef } from 'react'
import { Search, UserPlus, UserCheck, UserX, X, Upload, Camera } from 'lucide-react'
import { employeesAPI } from '../services/api'
import { initials, deptColor, riskBadge, fmtDate } from '../utils/helpers'
import toast from 'react-hot-toast'

const DEPARTMENTS = ['Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'Administration']
const ROLES       = ['employee', 'admin']

function Avatar({ employee, size = 'md' }) {
  const sizes = { sm: 'w-8 h-8 text-xs', md: 'w-10 h-10 text-sm', lg: 'w-16 h-16 text-xl' }
  const color = deptColor(employee.department)

  if (employee.avatar_url) {
    return (
      <img
        src={employee.avatar_url}
        alt={employee.full_name}
        className={`${sizes[size]} rounded-full object-cover border-2`}
        style={{ borderColor: color + '40' }}
        onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
      />
    )
  }

  return (
    <div
      className={`${sizes[size]} rounded-full flex items-center justify-center font-mono font-bold shrink-0`}
      style={{ backgroundColor: color + '18', color, border: `2px solid ${color}30` }}
    >
      {initials(employee.full_name)}
    </div>
  )
}

function RegisterModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({
    full_name: '', email: '', password: '', department: 'Engineering',
    position: '', phone: '', employee_code: '', role: 'employee', avatar_url: '',
  })
  const [preview,  setPreview]  = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [errors,   setErrors]   = useState({})
  const fileRef = useRef()

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (file.size > 2 * 1024 * 1024) { toast.error('Image must be under 2MB'); return }
    const reader = new FileReader()
    reader.onload = () => {
      setPreview(reader.result)
      set('avatar_url', reader.result)
    }
    reader.readAsDataURL(file)
  }

  const validate = () => {
    const e = {}
    if (!form.full_name.trim())  e.full_name = 'Required'
    if (!form.email.trim())      e.email     = 'Required'
    if (!form.password || form.password.length < 6) e.password = 'Min 6 characters'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const res = await employeesAPI.create(form)
      toast.success(`${form.full_name} registered successfully`)
      onSuccess(res.data.employee)
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to register employee')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-2xl bg-navy-800 border border-sentinel-border rounded-2xl shadow-2xl animate-fade-in overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-sentinel-border">
          <div>
            <h2 className="font-display font-bold text-lg text-sentinel-text">Register Employee</h2>
            <p className="text-xs font-mono text-sentinel-muted mt-0.5">Add a new employee to SENTINEL</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-navy-700 flex items-center justify-center text-sentinel-muted hover:text-sentinel-text transition-colors">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto max-h-[80vh]">
          {/* Avatar upload */}
          <div className="flex items-center gap-5 mb-6">
            <div className="relative">
              <div
                onClick={() => fileRef.current?.click()}
                className="w-20 h-20 rounded-full border-2 border-dashed border-sentinel-border hover:border-cyan-400/40 flex items-center justify-center cursor-pointer transition-all duration-200 overflow-hidden bg-navy-900 group"
              >
                {preview ? (
                  <img src={preview} alt="Preview" className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center gap-1 text-sentinel-muted group-hover:text-cyan-400 transition-colors">
                    <Camera size={20} />
                    <span className="text-[10px] font-mono">Photo</span>
                  </div>
                )}
              </div>
              {preview && (
                <button type="button" onClick={() => { setPreview(null); set('avatar_url', '') }}
                  className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                  <X size={10} className="text-white" />
                </button>
              )}
            </div>
            <input ref={fileRef} type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
            <div>
              <p className="text-sm text-sentinel-text font-medium">Profile Photo</p>
              <p className="text-xs font-mono text-sentinel-muted mt-1">JPG, PNG up to 2MB</p>
              <button type="button" onClick={() => fileRef.current?.click()}
                className="mt-2 flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors">
                <Upload size={12} /> Upload photo
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Full name */}
            <div className="md:col-span-2">
              <label className="label mb-1.5 block">Full Name *</label>
              <input value={form.full_name} onChange={e => set('full_name', e.target.value)}
                className={`input-field ${errors.full_name ? 'border-red-500/50' : ''}`} placeholder="Arjun Sharma" />
              {errors.full_name && <p className="text-red-400 text-xs font-mono mt-1">{errors.full_name}</p>}
            </div>

            {/* Email */}
            <div>
              <label className="label mb-1.5 block">Email *</label>
              <input type="email" value={form.email} onChange={e => set('email', e.target.value)}
                className={`input-field ${errors.email ? 'border-red-500/50' : ''}`} placeholder="arjun@company.com" />
              {errors.email && <p className="text-red-400 text-xs font-mono mt-1">{errors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="label mb-1.5 block">Password *</label>
              <input type="password" value={form.password} onChange={e => set('password', e.target.value)}
                className={`input-field ${errors.password ? 'border-red-500/50' : ''}`} placeholder="Min 6 characters" />
              {errors.password && <p className="text-red-400 text-xs font-mono mt-1">{errors.password}</p>}
            </div>

            {/* Department */}
            <div>
              <label className="label mb-1.5 block">Department</label>
              <select value={form.department} onChange={e => set('department', e.target.value)} className="input-field">
                {DEPARTMENTS.map(d => <option key={d}>{d}</option>)}
              </select>
            </div>

            {/* Role */}
            <div>
              <label className="label mb-1.5 block">Role</label>
              <select value={form.role} onChange={e => set('role', e.target.value)} className="input-field">
                {ROLES.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
              </select>
            </div>

            {/* Position */}
            <div>
              <label className="label mb-1.5 block">Position / Title</label>
              <input value={form.position} onChange={e => set('position', e.target.value)}
                className="input-field" placeholder="Senior Developer" />
            </div>

            {/* Employee code */}
            <div>
              <label className="label mb-1.5 block">Employee ID</label>
              <input value={form.employee_code} onChange={e => set('employee_code', e.target.value)}
                className="input-field" placeholder="EMP-001" />
            </div>

            {/* Phone */}
            <div className="md:col-span-2">
              <label className="label mb-1.5 block">Phone</label>
              <input value={form.phone} onChange={e => set('phone', e.target.value)}
                className="input-field" placeholder="+91 98765 43210" />
            </div>
          </div>

          {/* Footer */}
          <div className="flex gap-3 mt-6 pt-5 border-t border-sentinel-border">
            <button type="button" onClick={onClose} className="btn-ghost flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? (
                <><div className="w-4 h-4 border-2 border-navy-950/30 border-t-navy-950 rounded-full animate-spin" /> Registering...</>
              ) : (
                <><UserPlus size={14} /> Register Employee</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function EmployeeCard({ employee, onToggleActive }) {
  const color = deptColor(employee.department)
  return (
    <div className="card overflow-hidden transition-all duration-300 hover:border-cyan-400/15 animate-fade-in">
      {/* Top accent bar */}
      <div className="h-1 w-full" style={{ backgroundColor: color + '60' }} />

      <div className="p-5">
        {/* Avatar + name row */}
        <div className="flex items-center gap-3 mb-4">
          <Avatar employee={employee} size="md" />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sentinel-text text-sm leading-tight truncate">{employee.full_name}</p>
            <p className="text-xs font-mono mt-0.5 truncate" style={{ color }}>
              {employee.position || employee.department || '—'}
            </p>
          </div>
          <span className={`shrink-0 ${employee.is_active ? 'badge-low' : 'badge-critical'}`}>
            {employee.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>

        {/* Details */}
        <div className="space-y-1.5 mb-4">
          <p className="text-xs font-mono text-sentinel-muted truncate">{employee.email}</p>
          <div className="flex items-center gap-3">
            {employee.phone         && <p className="text-xs font-mono text-sentinel-muted">{employee.phone}</p>}
            {employee.employee_code && <p className="text-xs font-mono text-sentinel-muted">#{employee.employee_code}</p>}
          </div>
        </div>

        {/* Footer row */}
        <div className="flex items-center justify-between pt-3 border-t border-sentinel-border/50">
          <div className="flex items-center gap-2">
            <span className={riskBadge(employee.risk_score || 0)}>
              {Math.round(employee.risk_score || 0)}
            </span>
            <span className="badge-ok capitalize text-[10px]">{employee.role}</span>
          </div>
          <button
            onClick={() => onToggleActive(employee)}
            className={`flex items-center gap-1 text-[11px] font-mono px-2 py-1 rounded-md border transition-all duration-200
              ${employee.is_active
                ? 'border-red-500/20 text-red-400 hover:bg-red-400/10'
                : 'border-emerald-500/20 text-emerald-400 hover:bg-emerald-400/10'}`}
          >
            {employee.is_active ? <><UserX size={10} /> Deactivate</> : <><UserCheck size={10} /> Activate</>}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Employees() {
  const [employees, setEmployees] = useState([])
  const [filtered,  setFiltered]  = useState([])
  const [search,    setSearch]    = useState('')
  const [dept,      setDept]      = useState('all')
  const [view,      setView]      = useState('grid')
  const [loading,   setLoading]   = useState(true)
  const [showModal, setShowModal] = useState(false)

  const load = () => {
    setLoading(true)
    employeesAPI.getAll({ limit: 200 })
      .then(r => { setEmployees(r.data?.employees || []); setFiltered(r.data?.employees || []) })
      .catch(() => toast.error('Failed to load employees'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    let list = employees
    if (search) list = list.filter(e =>
      e.full_name.toLowerCase().includes(search.toLowerCase()) ||
      e.email.toLowerCase().includes(search.toLowerCase()) ||
      (e.employee_code || '').toLowerCase().includes(search.toLowerCase())
    )
    if (dept !== 'all') list = list.filter(e => e.department === dept)
    setFiltered(list)
  }, [search, dept, employees])

  const departments = ['all', ...new Set(employees.map(e => e.department).filter(Boolean))]

  const toggleActive = async (emp) => {
    try {
      await employeesAPI.update(emp.id, { is_active: !emp.is_active })
      setEmployees(prev => prev.map(e => e.id === emp.id ? { ...e, is_active: !e.is_active } : e))
      toast.success(`${emp.full_name} ${emp.is_active ? 'deactivated' : 'activated'}`)
    } catch { toast.error('Failed to update employee') }
  }

  const onRegisterSuccess = (newEmp) => {
    setEmployees(prev => [newEmp, ...prev])
  }

  return (
    <div className="space-y-5">
      {showModal && <RegisterModal onClose={() => setShowModal(false)} onSuccess={onRegisterSuccess} />}

      {/* Header */}
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <h1 className="font-display font-bold text-2xl text-sentinel-text">Employees</h1>
          <p className="text-sentinel-muted text-sm font-mono mt-1">{filtered.length} of {employees.length} shown</p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
          <UserPlus size={15} /> Register Employee
        </button>
      </div>

      <div className="glow-line" />

      {/* Filters */}
      <div className="flex flex-wrap gap-3 animate-fade-in stagger-1">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-sentinel-muted" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search name, email, or ID..." className="input-field pl-9" />
        </div>
        <select value={dept} onChange={e => setDept(e.target.value)} className="input-field w-auto">
          {departments.map(d => <option key={d} value={d}>{d === 'all' ? 'All Departments' : d}</option>)}
        </select>
        <div className="flex border border-sentinel-border rounded-lg overflow-hidden">
          {[['grid', '⊞'], ['list', '☰']].map(([v, icon]) => (
            <button key={v} onClick={() => setView(v)}
              className={`px-3 py-2 text-sm transition-colors ${view === v ? 'bg-cyan-400/10 text-cyan-400' : 'text-sentinel-muted hover:text-sentinel-text'}`}>
              {icon}
            </button>
          ))}
        </div>
      </div>

      {/* Grid view */}
      {view === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 animate-fade-in stagger-2">
          {loading ? (
            Array(6).fill(0).map((_, i) => (
              <div key={i} className="card p-5">
                <div className="flex gap-4">
                  <div className="w-16 h-16 rounded-full bg-navy-700 animate-pulse" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-navy-700 rounded animate-pulse w-3/4" />
                    <div className="h-3 bg-navy-700 rounded animate-pulse w-1/2" />
                    <div className="h-3 bg-navy-700 rounded animate-pulse w-2/3" />
                  </div>
                </div>
              </div>
            ))
          ) : filtered.length === 0 ? (
            <div className="col-span-3 card p-12 text-center">
              <p className="text-sentinel-muted font-mono">No employees found</p>
            </div>
          ) : (
            filtered.map(emp => (
              <EmployeeCard key={emp.id} employee={emp} onToggleActive={toggleActive} />
            ))
          )}
        </div>
      ) : (
        /* List view */
        <div className="card overflow-hidden animate-fade-in stagger-2">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-sentinel-border">
                  <th className="label text-left px-5 py-3">Employee</th>
                  <th className="label text-left px-5 py-3 hidden md:table-cell">Department</th>
                  <th className="label text-left px-5 py-3 hidden lg:table-cell">Position</th>
                  <th className="label text-left px-5 py-3 hidden lg:table-cell">Joined</th>
                  <th className="label text-left px-5 py-3">Risk</th>
                  <th className="label text-left px-5 py-3">Status</th>
                  <th className="label text-left px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array(6).fill(0).map((_, i) => (
                    <tr key={i} className="table-row">
                      <td colSpan={7} className="px-5 py-3">
                        <div className="h-4 bg-navy-700 rounded animate-pulse" />
                      </td>
                    </tr>
                  ))
                ) : filtered.map(emp => (
                  <tr key={emp.id} className="table-row">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        <Avatar employee={emp} size="sm" />
                        <div>
                          <p className="text-sm text-sentinel-text font-medium">{emp.full_name}</p>
                          <p className="text-[11px] font-mono text-sentinel-muted">{emp.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3 hidden md:table-cell">
                      <span className="text-sm font-mono" style={{ color: deptColor(emp.department) }}>{emp.department || '—'}</span>
                    </td>
                    <td className="px-5 py-3 hidden lg:table-cell">
                      <span className="text-sm text-sentinel-muted">{emp.position || '—'}</span>
                    </td>
                    <td className="px-5 py-3 hidden lg:table-cell">
                      <span className="text-sm font-mono text-sentinel-muted">{fmtDate(emp.created_at)}</span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={riskBadge(emp.risk_score || 0)}>{Math.round(emp.risk_score || 0)}</span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={emp.is_active ? 'badge-low' : 'badge-critical'}>
                        {emp.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <button onClick={() => toggleActive(emp)}
                        className={`flex items-center gap-1 text-xs font-mono px-2.5 py-1 rounded-lg border transition-all
                          ${emp.is_active ? 'border-red-500/20 text-red-400 hover:bg-red-400/10' : 'border-emerald-500/20 text-emerald-400 hover:bg-emerald-400/10'}`}>
                        {emp.is_active ? <UserX size={11} /> : <UserCheck size={11} />}
                        {emp.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}