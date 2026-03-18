import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/common/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Employees from './pages/Employees'
import Sessions from './pages/Sessions'
import Flags from './pages/Flags'
import Analytics from './pages/Analytics'
import Leaves from './pages/Leaves'
import Appeals from './pages/Appeals'
import AuditLog from './pages/AuditLog'
import Settings from './pages/Settings'

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  const user  = useAuthStore((s) => s.user)
  if (!token || !user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const initAuth = useAuthStore((s) => s.initAuth)
  useEffect(() => { initAuth() }, [])

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard"  element={<Dashboard />} />
        <Route path="employees"  element={<Employees />} />
        <Route path="sessions"   element={<Sessions />} />
        <Route path="flags"      element={<Flags />} />
        <Route path="analytics"  element={<Analytics />} />
        <Route path="leaves"     element={<Leaves />} />
        <Route path="appeals"    element={<Appeals />} />
        <Route path="audit"      element={<AuditLog />} />
        <Route path="settings"   element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
