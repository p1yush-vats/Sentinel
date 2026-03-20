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
          if (user.role !== 'admin' && user.role !== 'super_admin')
            throw new Error('Access denied. Admin credentials required.')
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          // Token expires in 24 hours
          const expiresAt = Date.now() + 24 * 60 * 60 * 1000

          set({ user, token: access_token, expiresAt, isLoading: false })
          return true
        } catch (err) {
          set({
            error: err.message || err.response?.data?.detail || 'Login failed',
            isLoading: false,
          })
          return false
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

        // Auto logout if token expired
        if (Date.now() > expiresAt) {
          console.log('Session expired, logging out...')
          delete api.defaults.headers.common['Authorization']
          set({ user: null, token: null, expiresAt: null })
          return
        }

        // Token still valid, restore auth header
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`

        // Schedule auto logout when token expires
        const msUntilExpiry = expiresAt - Date.now()
        setTimeout(() => {
          console.log('Token expired, auto logging out...')
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