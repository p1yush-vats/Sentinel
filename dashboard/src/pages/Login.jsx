import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useTheme, THEMES } from './ThemeContext'
import { useAuthStore } from '../store/authStore'

const NAV = [
  { path: '/my/dashboard', label: 'DASHBOARD',   short: 'HOME',     icon: '⌂' },
  { path: '/my/sessions',  label: 'MY SESSIONS',  short: 'SESSIONS', icon: '◷' },
  { path: '/my/flags',     label: 'MY FLAGS',     short: 'FLAGS',    icon: '⚑' },
  { path: '/my/leave',     label: 'LEAVE',        short: 'LEAVE',    icon: '◻' },
  { path: '/my/calendar',  label: 'CALENDAR',     short: 'CAL',      icon: '▦' },
]

export default function EmployeeLayout() {
  const { theme, themeName, setThemeName } = useTheme()
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [themeOpen,   setThemeOpen]   = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [avatarError, setAvatarError] = useState(false)

  // Close sidebar on route change
  useEffect(() => { setSidebarOpen(false) }, [location.pathname])

  const isAdmin   = user?.role === 'admin' || user?.role === 'super_admin'
  const initials  = (n) => n?.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || 'U'
  const hasAvatar = user?.avatar_url && !avatarError
  const t         = theme

  return (
    <div style={{
      display: 'flex', minHeight: '100vh',
      background: t.bg,
      fontFamily: "'DM Mono','IBM Plex Mono',monospace",
      color: t.text,
      overflowX: 'hidden',
    }}>

      {/* ───────── Injected responsive CSS ───────── */}
      <style>{`
        /* Large screens: sidebar is always visible, inlined */
        @media (min-width: 1024px) {
          .emp-sidebar   { position: sticky !important; top: 0 !important; height: 100vh !important; transform: translateX(0) !important; flex-shrink: 0 !important; }
          .emp-overlay   { display: none !important; }
          .emp-topbar    { display: none !important; }
          .emp-bottomnav { display: none !important; }
          .emp-body      { margin-left: 0 !important; }
          .emp-main      { padding: 28px 32px 32px !important; }
          .emp-close-btn { display: none !important; }
        }
        /* Smooth sidebar slide */
        .emp-sidebar { transition: transform 0.27s cubic-bezier(.4,0,.2,1); }
      `}</style>

      {/* ───────── Mobile overlay ───────── */}
      {sidebarOpen && (
        <div
          className="emp-overlay"
          onClick={() => setSidebarOpen(false)}
          style={{ position: 'fixed', inset: 0, zIndex: 40, background: 'rgba(0,0,0,0.72)', backdropFilter: 'blur(3px)' }}
        />
      )}

      {/* ───────── Sidebar ───────── */}
      <div
        className="emp-sidebar"
        style={{
          position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 50,
          width: 220,
          background: t.surface,
          borderRight: `2px solid ${t.border}`,
          display: 'flex', flexDirection: 'column',
          transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        }}
      >
        {/* Header */}
        <div style={{ padding: '20px 18px 16px', borderBottom: `2px solid ${t.border}` }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ fontSize: 8, letterSpacing: '3px', color: t.textMuted, fontWeight: 700 }}>
              SENTINEL // EMPLOYEE
            </div>
            <button
              className="emp-close-btn"
              onClick={() => setSidebarOpen(false)}
              style={{ background: 'transparent', border: 'none', color: t.textMuted, cursor: 'pointer', fontSize: 15, lineHeight: 1, padding: '2px 4px' }}
            >
              ✕
            </button>
          </div>
          {/* Avatar row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 40, height: 40, background: t.accent, color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 15, fontWeight: 900, overflow: 'hidden', flexShrink: 0,
            }}>
              {hasAvatar
                ? <img src={user.avatar_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={() => setAvatarError(true)} />
                : initials(user?.full_name)
              }
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: t.text, textTransform: 'uppercase', letterSpacing: '-0.3px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 120 }}>
                {user?.full_name?.split(' ')[0]}
              </div>
              <div style={{ fontSize: 9, color: t.textMuted, letterSpacing: '1px', marginTop: 2 }}>
                {user?.department || 'Employee'}
              </div>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav style={{ flex: 1, padding: '10px 0', overflowY: 'auto' }}>
          {NAV.map(item => {
            const active = location.pathname === item.path
            return (
              <div
                key={item.path}
                onClick={() => navigate(item.path)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '11px 18px',
                  fontSize: 10, letterSpacing: '2px', fontWeight: 700,
                  cursor: 'pointer',
                  background: active ? t.accent : 'transparent',
                  color: active ? '#fff' : t.textMuted,
                  borderLeft: active ? `4px solid ${t.text}` : '4px solid transparent',
                  transition: 'all 0.12s',
                  userSelect: 'none',
                  whiteSpace: 'nowrap',
                }}
                onMouseEnter={e => { if (!active) { e.currentTarget.style.color = t.text; e.currentTarget.style.background = t.card } }}
                onMouseLeave={e => { if (!active) { e.currentTarget.style.color = t.textMuted; e.currentTarget.style.background = 'transparent' } }}
              >
                <span style={{ fontSize: 14 }}>{item.icon}</span>
                {item.label}
              </div>
            )
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: '12px 18px', borderTop: `2px solid ${t.border}`, display: 'flex', flexDirection: 'column', gap: 8, position: 'relative' }}>
          {/* Theme dropdown (opens above) */}
          {themeOpen && (
            <div style={{
              position: 'absolute', bottom: '100%', left: 18, width: 180, marginBottom: 4,
              background: t.card, border: `2px solid ${t.border}`, zIndex: 200,
            }}>
              {Object.entries(THEMES).map(([key, th]) => (
                <div
                  key={key}
                  onClick={() => { setThemeName(key); setThemeOpen(false) }}
                  style={{
                    padding: '10px 14px', fontSize: 9, letterSpacing: '2px', fontWeight: 700,
                    cursor: 'pointer',
                    background: themeName === key ? t.accent : 'transparent',
                    color: themeName === key ? '#fff' : t.textMuted,
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}
                >
                  <span style={{ width: 10, height: 10, background: th.accent, display: 'inline-block' }} />
                  {th.name.toUpperCase()}
                </div>
              ))}
            </div>
          )}
          <button
            onClick={() => setThemeOpen(o => !o)}
            style={{
              width: '100%', padding: '7px 10px', background: 'transparent',
              border: `2px solid ${t.border}`, color: t.textMuted,
              fontSize: 9, letterSpacing: '2px', fontWeight: 700, cursor: 'pointer',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              fontFamily: 'inherit',
            }}
          >
            <span>THEME: {THEMES[themeName]?.name?.toUpperCase()}</span>
            <span>{themeOpen ? '▲' : '▼'}</span>
          </button>
          {isAdmin && (
            <button
              onClick={() => navigate('/dashboard')}
              style={{
                width: '100%', padding: '8px 10px', background: t.accent, border: 'none',
                color: '#fff', fontSize: 9, letterSpacing: '2px', fontWeight: 900,
                cursor: 'pointer', fontFamily: 'inherit',
              }}
            >
              → ADMIN VIEW
            </button>
          )}
          <button
            onClick={logout}
            style={{
              width: '100%', padding: '7px 10px', background: 'transparent',
              border: `2px solid ${t.border}`, color: t.textMuted,
              fontSize: 9, letterSpacing: '2px', fontWeight: 700,
              cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            SIGN OUT
          </button>
        </div>
      </div>

      {/* ───────── Right body ───────── */}
      <div
        className="emp-body"
        style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}
      >
        {/* Mobile top bar */}
        <div
          className="emp-topbar"
          style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '11px 16px',
            background: t.surface, borderBottom: `2px solid ${t.border}`,
            position: 'sticky', top: 0, zIndex: 30,
          }}
        >
          <button
            onClick={() => setSidebarOpen(true)}
            style={{
              background: 'transparent', border: `2px solid ${t.border}`, color: t.text,
              width: 36, height: 36, cursor: 'pointer', fontSize: 16,
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}
          >
            ☰
          </button>
          <div style={{ fontSize: 11, fontWeight: 900, letterSpacing: '3px', color: t.accent }}>
            SENTINEL
          </div>
          <div style={{ fontSize: 9, color: t.textMuted, letterSpacing: '2px', marginLeft: 2 }}>
            // {NAV.find(n => n.path === location.pathname)?.label || 'EMPLOYEE'}
          </div>
          {isAdmin && (
            <button
              onClick={() => navigate('/dashboard')}
              style={{
                marginLeft: 'auto', padding: '4px 10px', background: 'transparent',
                border: `2px solid ${t.border}`, color: t.textMuted,
                fontSize: 8, letterSpacing: '2px', fontWeight: 700,
                cursor: 'pointer', fontFamily: 'inherit', whiteSpace: 'nowrap',
              }}
            >
              ADMIN ↗
            </button>
          )}
        </div>

        {/* Page content */}
        <main
          className="emp-main"
          style={{
            flex: 1,
            padding: '20px 16px 88px', /* bottom padding so content clears the bottom nav */
            overflowY: 'auto', overflowX: 'hidden',
            minWidth: 0,
          }}
        >
          <div style={{ maxWidth: 900, margin: '0 auto' }}>
            <Outlet />
          </div>
        </main>

        {/* Mobile bottom nav */}
        <nav
          className="emp-bottomnav"
          style={{
            position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 30,
            background: t.surface, borderTop: `2px solid ${t.border}`,
            display: 'flex',
          }}
        >
          {NAV.map(item => {
            const active = location.pathname === item.path
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                style={{
                  flex: 1,
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center',
                  gap: 3, padding: '9px 4px 10px',
                  background: active ? `${t.accent}1a` : 'transparent',
                  border: 'none',
                  borderTop: `2px solid ${active ? t.accent : 'transparent'}`,
                  color: active ? t.accent : t.textMuted,
                  cursor: 'pointer', fontFamily: 'inherit',
                  transition: 'all 0.14s',
                }}
              >
                <span style={{ fontSize: 18, lineHeight: 1 }}>{item.icon}</span>
                <span style={{ fontSize: 7, letterSpacing: '1.5px', fontWeight: 700, marginTop: 2 }}>{item.short}</span>
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}