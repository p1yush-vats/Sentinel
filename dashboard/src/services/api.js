import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1', timeout: 15000 })

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

export const authAPI       = { login: (d)       => api.post('/auth/login', d), me: () => api.get('/auth/me'), logout: () => api.post('/auth/logout') }
export const employeesAPI  = { getAll: (p) => api.get('/employees/', { params: p }), getOne: (id) => api.get(`/employees/${id}`), create: (d) => api.post('/employees/', d), update: (id, d) => api.patch(`/employees/${id}`, d), remove: (id) => api.delete(`/employees/${id}`) }
export const sessionsAPI   = { getAll: (p)      => api.get('/sessions/all', { params: p }), getOne: (id) => api.get(`/sessions/${id}`), getLogs: (id) => api.get(`/sessions/${id}/logs`) }
export const flagsAPI      = { getUnreviewed: (p) => api.get('/abnormalities/all/unreviewed', { params: p }), review: (id, d) => api.post(`/abnormalities/${id}/review`, d), adminAction: (d) => api.post('/abnormalities/admin-actions', d) }
export const appealsAPI    = { getAll: (p)      => api.get('/appeals/all', { params: p }), review: (id, d) => api.post(`/appeals/${id}/review`, d) }
export const workRulesAPI  = { getAll: ()       => api.get('/work-rules/'), update: (id, d) => api.patch(`/work-rules/${id}`, d), create: (d) => api.post('/work-rules/', d) }
export const metricsAPI    = { getByEmployee: (id, p) => api.get(`/productivity-metrics/employee/${id}`, { params: p }) }
export const auditAPI      = { getAll: (p)      => api.get('/audit/', { params: p }) }