import { Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Sidebar from './Sidebar'
import { flagsAPI } from '../../services/api'

export default function Layout() {
  const [flagCount, setFlagCount] = useState(0)

  useEffect(() => {
    flagsAPI.getUnreviewed({ limit: 1 })
      .then(r => setFlagCount(r.data?.total || 0))
      .catch(() => {})

    const interval = setInterval(() => {
      flagsAPI.getUnreviewed({ limit: 1 })
        .then(r => setFlagCount(r.data?.total || 0))
        .catch(() => {})
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex min-h-screen bg-sentinel-bg grid-bg">
      <Sidebar flagCount={flagCount} />
      <main className="flex-1 overflow-auto">
        <div className="p-6 lg:p-8 animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
