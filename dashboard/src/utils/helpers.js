import { format, formatDistanceToNow, parseISO } from 'date-fns'

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

export const initials = (name) => {
  if (!name) return '??'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

export const deptColor = (dept) => {
  const map = {
    Engineering:  '#22d3ee',
    Sales:        '#10b981',
    Marketing:    '#f59e0b',
    Finance:      '#8b5cf6',
    HR:           '#ec4899',
    Operations:   '#f97316',
    Administration: '#64748b',
  }
  return map[dept] || '#64748b'
}

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