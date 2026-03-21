import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import {
  LayoutDashboard, Users, Clock, AlertTriangle, BarChart3,
  Calendar, MessageSquare, ScrollText, Settings, LogOut, Shield, X,
  ArrowLeftRight
} from 'lucide-react'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/employees', icon: Users,           label: 'Employees' },
  { to: '/sessions',  icon: Clock,           label: 'Sessions' },
  { to: '/flags',     icon: AlertTriangle,   label: 'Flags', badge: true },
  { to: '/analytics', icon: BarChart3,       label: 'Analytics' },
  { to: '/leaves',    icon: Calendar,        label: 'Leave Requests' },
  { to: '/appeals',   icon: MessageSquare,   label: 'Appeals' },
  { to: '/audit',     icon: ScrollText,      label: 'Audit Log' },
  { to: '/settings',  icon: Settings,        label: 'Settings' },
]

export default function Sidebar({ flagCount = 0, onClose }) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <aside className="w-64 h-full min-h-screen bg-navy-900 border-r border-sentinel-border flex flex-col">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-sentinel-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center">
            <Shield size={16} className="text-cyan-400" />
          </div>
          <div>
            <span className="font-display font-bold text-base text-sentinel-text tracking-wide">SENTINEL</span>
            <p className="text-[10px] font-mono text-sentinel-muted tracking-widest uppercase">Admin Console</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="lg:hidden w-7 h-7 rounded-lg hover:bg-navy-700 flex items-center justify-center text-sentinel-muted hover:text-sentinel-text transition-colors"
          >
            <X size={15} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label, badge }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) => isActive ? 'nav-item-active' : 'nav-item'}
          >
            <Icon size={16} />
            <span className="flex-1 truncate">{label}</span>
            {badge && flagCount > 0 && (
              <span className="bg-red-500 text-white text-[10px] font-mono px-1.5 py-0.5 rounded-full min-w-[18px] text-center shrink-0">
                {flagCount > 99 ? '99+' : flagCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Employee view toggle */}
      <div className="px-3 pb-2">
        <button
          onClick={() => navigate('/my/dashboard')}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-mono border border-cyan-400/20 text-cyan-400 hover:bg-cyan-400/10 transition-all duration-200"
        >
          <ArrowLeftRight size={14} />
          <span className="flex-1 text-left text-xs">Switch to Employee View</span>
        </button>
      </div>

      {/* User */}
      <div className="p-3 border-t border-sentinel-border shrink-0">
        <div className="flex items-center gap-3 px-2 py-2 mb-1">
          <div className="w-8 h-8 rounded-full bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center text-xs font-mono text-cyan-400 font-bold shrink-0">
            {user?.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-sentinel-text truncate font-medium">{user?.full_name}</p>
            <p className="text-[10px] font-mono text-sentinel-muted uppercase tracking-wider truncate">{user?.role?.replace('_', ' ')}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-sentinel-muted hover:text-red-400 hover:bg-red-400/5 rounded-lg transition-all duration-200"
        >
          <LogOut size={14} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  )
}