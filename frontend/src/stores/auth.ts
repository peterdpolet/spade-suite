import { defineStore } from 'pinia'
import client from '../api/client'

interface User {
  id: number
  username: string
  email: string
}

interface AuthState {
  user: User | null
  access: string | null
  refresh: string | null
  loading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    access: localStorage.getItem('access'),
    refresh: localStorage.getItem('refresh'),
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.access,
  },

  actions: {
    async register(email: string, username: string, password: string, rePassword: string) {
      this.loading = true
      this.error = null
      try {
        await client.post('/api/auth/users/', {
          email,
          username,
          password,
          re_password: rePassword,
        })
      } catch (err: any) {
        this.error = formatDjoserError(err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async login(email: string, password: string) {
      this.loading = true
      this.error = null
      try {
        const { data } = await client.post('/api/auth/jwt/create/', { email, password })
        this.access = data.access
        this.refresh = data.refresh
        localStorage.setItem('access', data.access)
        localStorage.setItem('refresh', data.refresh)
        await this.fetchUser()
      } catch (err: any) {
        this.error = formatDjoserError(err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchUser() {
      const { data } = await client.get('/api/auth/users/me/')
      this.user = data
    },

    logout() {
      this.user = null
      this.access = null
      this.refresh = null
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
    },
  },
})

// Djoser error responses are field-keyed arrays, e.g.
// {"email": ["already exists"], "re_password": ["required"]} —
// flatten to one readable string for display.
function formatDjoserError(err: any): string {
  const data = err?.response?.data
  if (!data) return 'Something went wrong. Please try again.'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  return Object.entries(data)
    .map(([field, msgs]) => `${field}: ${(msgs as string[]).join(', ')}`)
    .join(' | ')
}
