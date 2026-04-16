import { format, formatDistanceToNow, parseISO } from 'date-fns'

// ─── Date Helpers ─────────────────────────────────────────────────────────────
// Ensure the ISO string is treated as UTC even if it has no timezone suffix.
// Supabase / SQLAlchemy returns "2026-03-19T08:30:00" (no Z) for
// "timestamp without time zone" columns — browsers interpret that as LOCAL
// time, which is wrong. Appending Z forces UTC interpretation.
function toUTC(iso) {
  if (!iso) return iso
  // Already has timezone info (+05:30, Z, etc.) — leave it alone
  if (iso.includes('Z') || iso.includes('+') || (iso.includes('-') && iso.lastIndexOf('-') > 7)) {
    return iso
  }
  return iso + 'Z'
}

export const fmt = (iso) => {
  if (!iso) return '—'
  try { return format(parseISO(toUTC(iso)), 'MMM d, yyyy HH:mm') } catch { return iso }
}

export const fmtDate = (iso) => {
  if (!iso) return '—'
  try { return format(parseISO(toUTC(iso)), 'MMM d, yyyy') } catch { return iso }
}

export const fromNow = (iso) => {
  if (!iso) return '—'
  try { return formatDistanceToNow(parseISO(toUTC(iso)), { addSuffix: true }) } catch { return iso }
}

export const fmtMins = (mins) => {
  if (mins == null) return '—'
  const h = Math.floor(mins / 60)
  const m = mins % 60
  if (h === 0) return `${m}m`
  return m === 0 ? `${h}h` : `${h}h ${m}m`
}


// ─── Risk & Severity ──────────────────────────────────────────────────────────

export const riskColor = (score) => {
  if (score >= 75) return 'text-red-400'
  if (score >= 50) return 'text-orange-400'
  if (score >= 25) return 'text-amber-400'
  return 'text-emerald-400'
}

export const riskBadge = (score) => {
  if (score >= 75) return 'badge-critical'
  if (score >= 50) return 'badge-high'
  if (score >= 25) return 'badge-medium'
  return 'badge-low'
}

export const severityBadge = (s) => {
  const map = { CRITICAL: 'badge-critical', HIGH: 'badge-high', MEDIUM: 'badge-medium', LOW: 'badge-low' }
  return map[s] || 'badge-ok'
}


// ─── User ─────────────────────────────────────────────────────────────────────

export const initials = (name) => {
  if (!name) return '??'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}


// ─── Department Colours ───────────────────────────────────────────────────────

const DEPT_COLORS = {
  // Departments from employee table
  Engineering:    '#22d3ee',   // cyan
  Sales:          '#10b981',   // emerald
  Marketing:      '#f59e0b',   // amber
  Finance:        '#8b5cf6',   // violet
  HR:             '#ec4899',   // pink
  IT:             '#3b82f6',   // blue
  Administration: '#64748b',   // slate

  // Extended / future departments
  Operations:     '#f97316',   // orange
  Legal:          '#a855f7',   // purple
  Design:         '#e11d48',   // rose
  Product:        '#0ea5e9',   // sky
  Support:        '#14b8a6',   // teal
  Logistics:      '#84cc16',   // lime
  Procurement:    '#eab308',   // yellow
  Security:       '#6366f1',   // indigo
  Research:       '#06b6d4',   // light cyan
}

// Returns the solid hex colour for a department
export const deptColor = (dept) => DEPT_COLORS[dept] || '#64748b'

// Returns a low-opacity background (useful for badge/chip backgrounds)
export const deptBg = (dept) => `${deptColor(dept)}22`

// Returns a ready-to-spread inline style object { color, background, border }
export const deptStyle = (dept) => ({
  color:      deptColor(dept),
  background: deptBg(dept),
  border:     `1px solid ${deptColor(dept)}44`,
})


// ─── Status ───────────────────────────────────────────────────────────────────

export const statusBadge = (status) => {
  const map = {
    active:    'badge-ok',
    completed: 'badge-low',
    flagged:   'badge-high',
    partial:   'badge-medium',
    abandoned: 'badge-critical',
  }
  return map[status] || 'badge-ok'
}