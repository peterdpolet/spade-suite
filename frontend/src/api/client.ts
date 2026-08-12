import axios from 'axios'

const client = axios.create({
  baseURL: '',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const access = localStorage.getItem('access')
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

let isRefreshing = false
let pendingQueue: Array<() => void> = []

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    const refresh = localStorage.getItem('refresh')
    if (!refresh) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    if (isRefreshing) {
      return new Promise((resolve) => {
        pendingQueue.push(() => resolve(client(originalRequest)))
      })
    }

    isRefreshing = true
    try {
      const { data } = await axios.post('/api/auth/jwt/refresh/', { refresh })
      localStorage.setItem('access', data.access)
      // ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION are both True
      // (config/settings/base.py) — every successful refresh blacklists
      // the OLD refresh token and issues a NEW one. Must persist it here,
      // or the *next* refresh attempt reuses a now-blacklisted token and
      // is guaranteed to 401.
      if (data.refresh) {
        localStorage.setItem('refresh', data.refresh)
      }
      pendingQueue.forEach((cb) => cb())
      pendingQueue = []
      return client(originalRequest)
    } catch (refreshError) {
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      pendingQueue = []
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default client
