// =============================================================
// client.js - centralized Axios instance
// =============================================================
// Responsibilities:
//   - base URL from VITE_API_URL (never hardcoded)
//   - attach the access token to every request
//   - on 401, try the refresh token once, then replay the request
//   - if refresh fails, clear the session and redirect to /login
//   - normalize backend errors into ApiError
// =============================================================

import axios from 'axios'

export const ACCESS_KEY = 'access_token'
export const REFRESH_KEY = 'refresh_token'

export class ApiError extends Error {
  constructor(code, message, status) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_KEY)
  if (token && !config.skipAuth) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Single-flight refresh: many parallel 401s trigger only one refresh call.
let refreshing = null

async function runRefresh() {
  const refreshToken = localStorage.getItem(REFRESH_KEY)
  if (!refreshToken) throw new Error('no refresh token')
  const { data } = await api.post(
    '/auth/refresh',
    { refresh_token: refreshToken },
    { skipAuth: true },
  )
  localStorage.setItem(ACCESS_KEY, data.access_token)
  localStorage.setItem(REFRESH_KEY, data.refresh_token)
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!error.response) {
      throw new ApiError('network_error', 'Cannot reach the server.', 0)
    }

    const { status, data, config } = error.response
    const url = config?.url ?? ''
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/refresh')

    if (status === 401 && !isAuthCall && !config._retried) {
      try {
        config._retried = true
        if (!refreshing) refreshing = runRefresh().finally(() => (refreshing = null))
        await refreshing
        config.headers.Authorization = `Bearer ${localStorage.getItem(ACCESS_KEY)}`
        return api.request(config)
      } catch {
        localStorage.removeItem(ACCESS_KEY)
        localStorage.removeItem(REFRESH_KEY)
        if (!location.pathname.startsWith('/login')) {
          location.assign('/login?expired=1')
        }
        throw new ApiError('session_expired', 'Your session has expired.', 401)
      }
    }

    throw new ApiError(
      data?.code ?? 'error',
      data?.message ?? error.message ?? 'Request failed',
      status,
    )
  },
)
