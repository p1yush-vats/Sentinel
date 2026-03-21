import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useTheme, THEMES } from './ThemeContext'
import { useAuthStore } from '../store/authStore'

const NAV = [
  { path: '/my/dashboard', label: 'DASHBOARD',  icon: '⌂' },
  { path: '/my/sessions',  label: 'MY SESSIONS', icon: '◷' },
  { path: '/my/flags',     label: 'MY FLAGS',    icon: '⚑' },
  { path: '/my/leave',     label: 'LEAVE',       icon: '◻' },
  { path: '/my/appeals',   label: 'APPEALS',     icon: '◈' },
  { path: '/my/calendar',  label: 'CALENDAR',    icon: '▦' },
]

export default function EmployeeLayout() {
  const { theme, themeName, setThemeName, THEMES } = useTheme()
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [themeOpen, setThemeOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'

  const s = {
    shell: {
      display: 'flex',
      minHeight: '100vh',
      background: theme.bg,
      fontFamily: "'DM Mono', 'IBM Plex Mono', monospace",
      color: theme.text,
      transition: 'background 0.3s, color 0.3s',
    },
    sidebar: {
      width: '220px',
      minHeight: '100vh',
      background: theme.surface,
      borderRight: `2px solid ${theme.border}`,
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      position: 'sticky',
      top: 0,
      height: '100vh',
      overflow: 'hidden',
    },
    sideHeader: {
      padding: '24px 20px 20px',
      borderBottom: `2px solid ${theme.border}`,
    },
    sysLabel: {
      fontSize: '9px',
      letterSpacing: '3px',
      color: theme.textMuted,
      textTransform: 'uppercase',
      marginBottom: '12px',
    },
    avatar: {
      width: '44px',
      height: '44px',
      background: theme.accent,
      color: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '16px',
      fontWeight: '900',
      letterSpacing: '-1px',
      marginBottom: '10px',
    },
    userName: {
      fontSize: '13px',
      fontWeight: '700',
      letterSpacing: '-0.5px',
      color: theme.text,
      textTransform: 'uppercase',
    },
    userDept: {
      fontSize: '10px',
      color: theme.textMuted,
      letterSpacing: '1px',
      marginTop: '2px',
    },
    nav: {
      flex: 1,
      padding: '16px 0',
      overflowY: 'auto',
    },
    navItem: (active) => ({
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      padding: '11px 20px',
      fontSize: '10px',
      letterSpacing: '2px',
      fontWeight: '700',
      cursor: 'pointer',
      background: active ? theme.accent : 'transparent',
      color: active ? '#fff' : theme.textMuted,
      borderLeft: active ? `4px solid ${theme.text}` : '4px solid transparent',
      transition: 'all 0.15s',
      userSelect: 'none',
    }),
    sideFooter: {
      padding: '16px 20px',
      borderTop: `2px solid ${theme.border}`,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
    },
    themeBtn: {
      width: '100%',
      padding: '8px 12px',
      background: 'transparent',
      border: `2px solid ${theme.border}`,
      color: theme.textMuted,
      fontSize: '9px',
      letterSpacing: '2px',
      fontWeight: '700',
      cursor: 'pointer',
      textAlign: 'left',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    themeDropdown: {
      position: 'absolute',
      bottom: '120px',
      left: '20px',
      width: '180px',
      background: theme.card,
      border: `2px solid ${theme.border}`,
      zIndex: 100,
    },
    themeOption: (active) => ({
      padding: '10px 14px',
      fontSize: '10px',
      letterSpacing: '2px',
      fontWeight: '700',
      cursor: 'pointer',
      background: active ? theme.accent : 'transparent',
      color: active ? '#fff' : theme.textMuted,
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    }),
    adminBtn: {
      width: '100%',
      padding: '8px 12px',
      background: theme.accent,
      border: 'none',
      color: '#fff',
      fontSize: '9px',
      letterSpacing: '2px',
      fontWeight: '900',
      cursor: 'pointer',
      textAlign: 'center',
    },
    logoutBtn: {
      width: '100%',
      padding: '8px 12px',
      background: 'transparent',
      border: `2px solid ${theme.border}`,
      color: theme.textMuted,
      fontSize: '9px',
      letterSpacing: '2px',
      fontWeight: '700',
      cursor: 'pointer',
      textAlign: 'center',
    },
    main: {
      flex: 1,
      padding: '32px',
      minWidth: 0,
      overflowX: 'hidden',
    },
  }

  const initials = (name) => name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0,2) || 'U'

  return (
    <div style={s.shell}>
      {/* Sidebar */}
      <div style={s.sidebar}>
        <div style={s.sideHeader}>
          <div style={s.sysLabel}>SENTINEL // EMPLOYEE</div>
          <div style={s.avatar}>{initials(user?.full_name)}</div>
          <div style={s.userName}>{user?.full_name?.split(' ')[0]}</div>
          <div style={s.userDept}>{user?.department || 'Employee'}</div>
        </div>

        <div style={s.nav}>
          {NAV.map(item => {
            const active = location.pathname === item.path
            return (
              <div
                key={item.path}
                style={s.navItem(active)}
                onClick={() => navigate(item.path)}
                onMouseEnter={e => { if (!active) { e.currentTarget.style.color = theme.text; e.currentTarget.style.background = theme.card } }}
                onMouseLeave={e => { if (!active) { e.currentTarget.style.color = theme.textMuted; e.currentTarget.style.background = 'transparent' } }}
              >
                <span style={{ fontSize: '14px' }}>{item.icon}</span>
                {item.label}
              </div>
            )
          })}
        </div>

        <div style={{ ...s.sideFooter, position: 'relative' }}>
          {/* Theme picker */}
          {themeOpen && (
            <div style={s.themeDropdown}>
              {Object.entries(THEMES).map(([key, t]) => (
                <div
                  key={key}
                  style={s.themeOption(themeName === key)}
                  onClick={() => { setThemeName(key); setThemeOpen(false) }}
                >
                  <span style={{ width: '10px', height: '10px', background: t.accent, display: 'inline-block' }} />
                  {t.name.toUpperCase()}
                </div>
              ))}
            </div>
          )}

          <button style={s.themeBtn} onClick={() => setThemeOpen(o => !o)}>
            <span>THEME: {THEMES[themeName]?.name?.toUpperCase()}</span>
            <span>{themeOpen ? '▲' : '▼'}</span>
          </button>

          {isAdmin && (
            <button style={s.adminBtn} onClick={() => navigate('/dashboard')}>
              → ADMIN VIEW
            </button>
          )}

          <button style={s.logoutBtn} onClick={logout}>
            SIGN OUT
          </button>
        </div>
      </div>

      {/* Main content */}
      <main style={s.main}>
        <Outlet />
      </main>
    </div>
  )
}
