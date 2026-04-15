import axios from 'axios'

const api = axios.create({ 
  baseURL: import.meta.env.VITE_API_URL || '/api/v1', 
  timeout: 15000 
})
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('sentinel-auth')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// ── Auth ─────────────────────────────────────────────────────
export const authAPI = {
  login:  (d) => api.post('/auth/login', d),
  me:     ()  => api.get('/auth/me'),
  logout: ()  => api.post('/auth/logout'),
}

// ── Admin: Employees ──────────────────────────────────────────
export const employeesAPI = {
  getAll:    (p)      => api.get('/employees/', { params: p }),
  getOne:    (id)     => api.get(`/employees/${id}`),
  create:    (d)      => api.post('/employees/', d),
  update:    (id, d)  => api.patch(`/employees/${id}`, d),
  remove:    (id)     => api.delete(`/employees/${id}`),
  sendAlert: (id, d)  => api.post(`/employees/${id}/alert`, d),
}

// ── Sessions (admin + employee) ───────────────────────────────
export const sessionsAPI = {
  // Admin
  getAll:       (p)  => api.get('/sessions/all', { params: p }),
  getOne:       (id) => api.get(`/sessions/${id}`),
  getLogs:      (id) => api.get(`/sessions/${id}/logs`),
  // Employee — own sessions only
  getMySessions: (p) => api.get('/sessions/', { params: p }),
}

// ── Flags / Abnormalities ─────────────────────────────────────
export const flagsAPI = {
  // Admin
  getUnreviewed: (p)      => api.get('/abnormalities/all/unreviewed', { params: p }),
  getAll:        (p)      => api.get('/abnormalities/', { params: p }),
  review:        (id, d)  => api.post(`/abnormalities/${id}/review`, d),
  adminAction:   (d)      => api.post('/abnormalities/admin-actions', d),
  // Employee — own flags
  getMyFlags:    (p)      => api.get('/abnormalities/', { params: p }),
}

// ── Appeals ───────────────────────────────────────────────────
export const appealsAPI = {
  // Admin
  getAll:       (p)      => api.get('/appeals/all', { params: p }),
  review:       (id, d)  => api.post(`/appeals/${id}/review`, d),
  // Employee
  getMyAppeals: (p)      => api.get('/appeals/', { params: p }),
  submit:       (d)      => api.post('/appeals/', d),
}

// ── Work rules ────────────────────────────────────────────────
export const workRulesAPI = {
  getAll:  ()       => api.get('/work-rules/'),
  update:  (id, d)  => api.patch(`/work-rules/${id}`, d),
  create:  (d)      => api.post('/work-rules/', d),
  remove:  (id)     => api.delete(`/work-rules/${id}`),
}

// ── Metrics ───────────────────────────────────────────────────
export const metricsAPI = {
  getByEmployee: (id, p) => api.get(`/productivity-metrics/employee/${id}`, { params: p }),
  getBySession:  (id)    => api.get(`/productivity-metrics/session/${id}`),
}

// ── Audit ─────────────────────────────────────────────────────
export const auditAPI = {
  getAll: (p) => api.get('/audit/', { params: p }),
}

// ── Notification Preferences ──────────────────────────────────
export const notificationPrefsAPI = {
  getMe:   ()  => api.get('/notification-prefs/me'),
  updateMe: (d) => api.patch('/notification-prefs/me', d),
}

// ── Tasks ─────────────────────────────────────────────────────
export const tasksAPI = {
  // Admin
  getAll:  (p)      => api.get('/tasks/all', { params: p }),
  create:  (d)      => api.post('/tasks/', d),
  remove:  (id)     => api.delete(`/tasks/${id}`),
  // Employee
  getMy:   (p)      => api.get('/tasks/my', { params: p }),
  updateStatus: (id, d) => api.patch(`/tasks/${id}/status`, d),
}