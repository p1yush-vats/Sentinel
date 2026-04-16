import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

// ─── Desktop App Token Handoff ───────────────────────────────
// When the desktop app launches the portal via webbrowser.open(),
// it appends the JWT as a URL hash:  /my/sessions#token=eyJ...
// We read it here, hydrate the store, then wipe the hash so the
// token never sits in browser history.
async function _tryDesktopTokenHandoff() {
  try {
    const hash   = window.location.hash            // '#token=eyJ...'
    const search = window.location.search          // '?token=eyJ...' fallback
    let raw = null

    if (hash.startsWith('#token=')) {
      raw = decodeURIComponent(hash.slice(7))
    } else {
      const sp = new URLSearchParams(search)
      if (sp.has('token')) raw = sp.get('token')
    }

    if (!raw) return null

    // Wipe token from URL immediately — don't leave it in history
    const clean = window.location.origin + window.location.pathname;
    window.history.replaceState(null, '', clean)

    // Validate & fetch user profile with this token
    api.defaults.headers.common['Authorization'] = `Bearer ${raw}`
    const res  = await api.get('/auth/me')
    const user = res.data

    const expiresAt = Date.now() + 24 * 60 * 60 * 1000
    return { token: raw, user, expiresAt }
  } catch {
    delete api.defaults.headers.common['Authorization']
    return null
  }
}

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      expiresAt: null,
      isLoading: false,
      isInitializing: true, // Prevents premature redirect to login
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          const res = await api.post('/auth/login', { email, password })
          const { access_token, user } = res.data

          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          const expiresAt = Date.now() + 24 * 60 * 60 * 1000
          set({ user, token: access_token, expiresAt, isLoading: false })

          // Return role so Login.jsx can redirect correctly
          return { success: true, role: user.role }
        } catch (err) {
          set({
            error: err.message || err.response?.data?.detail || 'Login failed',
            isLoading: false,
          })
          return { success: false }
        }
      },

      logout: () => {
        delete api.defaults.headers.common['Authorization']
        set({ user: null, token: null, expiresAt: null, error: null })
      },

      clearError: () => set({ error: null }),

      initAuth: async () => {
        // 1. Check for desktop-app token handoff in URL first
        const handoff = await _tryDesktopTokenHandoff()
        if (handoff) {
          api.defaults.headers.common['Authorization'] = `Bearer ${handoff.token}`
          set({ token: handoff.token, user: handoff.user, expiresAt: handoff.expiresAt, isInitializing: false })
          return
        }

        // 2. Normal persisted-token path
        const { token, expiresAt } = get()
        if (!token) {
          set({ isInitializing: false })
          return
        }

        if (Date.now() > expiresAt) {
          delete api.defaults.headers.common['Authorization']
          set({ user: null, token: null, expiresAt: null, isInitializing: false })
          return
        }

        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        set({ isInitializing: false })

        const msUntilExpiry = expiresAt - Date.now()
        setTimeout(() => {
          delete api.defaults.headers.common['Authorization']
          set({ user: null, token: null, expiresAt: null })
          window.location.href = '/login'
        }, msUntilExpiry)
      },
    }),
    {
      name: 'sentinel-auth',
      partialize: (s) => ({
        user: s.user,
        token: s.token,
        expiresAt: s.expiresAt,
      }),
    }
  )
)