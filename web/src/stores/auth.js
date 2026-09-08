// =============================================================
// auth.js - authentication Pinia store
// =============================================================
// Exposes: currentUser, accessToken, isAuthenticated, isAdmin,
//          login(), logout(), refreshToken(), fetchCurrentUser()
// =============================================================

import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import { api, ACCESS_KEY, REFRESH_KEY } from '@/api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    currentUser: null,
    accessToken: localStorage.getItem(ACCESS_KEY),
    refreshTokenValue: localStorage.getItem(REFRESH_KEY),
    ready: false, // true once the initial fetchCurrentUser settled
  }),

  getters: {
    isAuthenticated: (s) => !!s.accessToken && !!s.currentUser,
    isAdmin: (s) => s.currentUser?.role === 'ADMIN',
  },

  actions: {
    _storeTokens(access, refresh) {
      this.accessToken = access
      this.refreshTokenValue = refresh
      localStorage.setItem(ACCESS_KEY, access)
      localStorage.setItem(REFRESH_KEY, refresh)
    },

    async login(username, password) {
      const tokens = await authApi.login(username, password)
      this._storeTokens(tokens.access_token, tokens.refresh_token)
      await this.fetchCurrentUser()
    },

    async register(payload) {
      const res = await authApi.register(payload)
      this._storeTokens(res.tokens.access_token, res.tokens.refresh_token)
      this.currentUser = res.user
    },

    async fetchCurrentUser() {
      try {
        this.currentUser = await authApi.me()
      } catch {
        this.currentUser = null
      } finally {
        this.ready = true
      }
    },

    // Explicit refresh (the axios interceptor also refreshes transparently).
    async refreshToken() {
      const { data } = await api.post(
        '/auth/refresh',
        { refresh_token: this.refreshTokenValue },
        { skipAuth: true },
      )
      this._storeTokens(data.access_token, data.refresh_token)
    },

    logout() {
      this.currentUser = null
      this.accessToken = null
      this.refreshTokenValue = null
      localStorage.removeItem(ACCESS_KEY)
      localStorage.removeItem(REFRESH_KEY)
    },
  },
})
