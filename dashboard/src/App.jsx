import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { ThemeProvider } from './employee/ThemeContext'
import Layout from './components/common/Layout'
import EmployeeLayout from './employee/EmployeeLayout'
import Login from './pages/Login'

// Admin pages
import Dashboard from './pages/Dashboard'
import Employees from './pages/Employees'
import EmployeeDetail from './pages/EmployeeDetail'
import Sessions from './pages/Sessions'
import Flags from './pages/Flags'
import Analytics from './pages/Analytics'
import Leaves from './pages/Leaves'
import Appeals from './pages/Appeals'
import AuditLog from './pages/AuditLog'
import Settings from './pages/Settings'

// Employee pages
import MyDashboard from './employee/MyDashboard'
import MySessions from './employee/MySessions'
import MyFlags from './employee/MyFlags'
import MyLeave from './employee/MyLeave'
import MyCalendar from './employee/MyCalendar'

function AdminRoute({ children }) {
  const { token, user } = useAuthStore()
  if (!token || !user) return <Navigate to="/login" replace />
  const isAdmin = user.role === 'admin' || user.role === 'super_admin'
  if (!isAdmin) return <Navigate to="/my/dashboard" replace />
  return children
}

function EmployeeRoute({ children }) {
  const { token, user } = useAuthStore()
  if (!token || !user) return <Navigate to="/login" replace />
  return children
}

function RootRedirect() {
  const { token, user } = useAuthStore()
  if (!token || !user) return <Navigate to="/login" replace />
  const isAdmin = user.role === 'admin' || user.role === 'super_admin'
  return <Navigate to={isAdmin ? '/dashboard' : '/my/dashboard'} replace />
}

export default function App() {
  const initAuth = useAuthStore((s) => s.initAuth)
  useEffect(() => { initAuth() }, [])

  return (
    <ThemeProvider>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* Root redirect based on role */}
        <Route path="/" element={<RootRedirect />} />

        {/* Admin routes */}
        <Route path="/" element={<AdminRoute><Layout /></AdminRoute>}>
          <Route path="dashboard"          element={<Dashboard />} />
          <Route path="employees"          element={<Employees />} />
          <Route path="employees/:id"      element={<EmployeeDetail />} />
          <Route path="sessions"           element={<Sessions />} />
          <Route path="flags"              element={<Flags />} />
          <Route path="analytics"          element={<Analytics />} />
          <Route path="leaves"             element={<Leaves />} />
          <Route path="appeals"            element={<Appeals />} />
          <Route path="audit"              element={<AuditLog />} />
          <Route path="settings"           element={<Settings />} />
        </Route>

        {/* Employee routes */}
        <Route path="/my" element={<EmployeeRoute><EmployeeLayout /></EmployeeRoute>}>
          <Route index element={<Navigate to="/my/dashboard" replace />} />
          <Route path="dashboard" element={<MyDashboard />} />
          <Route path="sessions"  element={<MySessions />} />
          <Route path="flags"     element={<MyFlags />} />
          <Route path="leave"     element={<MyLeave />} />
          <Route path="calendar"  element={<MyCalendar />} />
        </Route>

        <Route path="*" element={<RootRedirect />} />
      </Routes>
    </ThemeProvider>
  )
}