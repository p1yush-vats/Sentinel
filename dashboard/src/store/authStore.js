import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null, token: null, isLoading: false, error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          const res = await api.post('/auth/login', { email, password })
          const { access_token, user } = res.data
          if (user.role !== 'admin' && user.role !== 'super_admin')
            throw new Error('Access denied. Admin credentials required.')
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          set({ user, token: access_token, isLoading: false })
          return true
        } catch (err) {
          set({ error: err.message || err.response?.data?.detail || 'Login failed', isLoading: false })
          return false
        }
      },

      logout: () => {
        delete api.defaults.headers.common['Authorization']
        set({ user: null, token: null, error: null })
      },

      clearError: () => set({ error: null }),

      initAuth: () => {
        const { token } = get()
        if (token) api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      },
    }),
    { name: 'sentinel-auth', partialize: (s) => ({ user: s.user, token: s.token }) }
  )
)
