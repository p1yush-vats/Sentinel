import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      expiresAt: null,
      isLoading: false,
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

      initAuth: () => {
        const { token, expiresAt } = get()
        if (!token) return

        if (Date.now() > expiresAt) {
          delete api.defaults.headers.common['Authorization']
          set({ user: null, token: null, expiresAt: null })
          return
        }

        api.defaults.headers.common['Authorization'] = `Bearer ${token}`

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