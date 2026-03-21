import { Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Sidebar from './Sidebar'
import { flagsAPI } from '../../services/api'
import { Menu } from 'lucide-react'

export default function Layout() {
  const [flagCount,   setFlagCount]   = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const fetch = () => {
      flagsAPI.getUnreviewed({ limit: 100 })
        .then(r => setFlagCount(r.data?.total || r.data?.abnormalities?.length || 0))
        .catch(() => {})
    }
    fetch()
    const interval = setInterval(fetch, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }} className="bg-sentinel-bg grid-bg">

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — fixed height, never scrolls with page */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-64 transform transition-transform duration-300 ease-in-out
        lg:static lg:translate-x-0 lg:z-auto lg:flex-shrink-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `} style={{ height: '100vh' }}>
        <Sidebar flagCount={flagCount} onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main content — scrolls independently */}
      <main style={{ flex: 1, overflowY: 'auto', minWidth: 0 }}>

        {/* Mobile top bar */}
        <div className="lg:hidden flex items-center gap-3 px-4 py-3 bg-navy-900 border-b border-sentinel-border sticky top-0 z-10">
          <button
            onClick={() => setSidebarOpen(true)}
            className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-navy-700 text-sentinel-muted hover:text-sentinel-text transition-colors"
          >
            <Menu size={20} />
          </button>
          <span className="font-display font-bold text-base text-cyan-400 tracking-wide">SENTINEL</span>
          {flagCount > 0 && (
            <span className="ml-auto bg-red-500 text-white text-[10px] font-mono px-2 py-0.5 rounded-full">
              {flagCount} flags
            </span>
          )}
        </div>

        <div className="p-4 lg:p-6 xl:p-8 animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  )
}