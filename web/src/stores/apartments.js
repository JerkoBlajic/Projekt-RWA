// =============================================================
// apartments.js - business Pinia store for apartments
// =============================================================

import { defineStore } from 'pinia'
import { apartmentsApi } from '@/api/apartments'

export const useApartmentsStore = defineStore('apartments', {
  state: () => ({
    items: [],
    current: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchAll(params = {}) {
      this.loading = true
      this.error = null
      try {
        this.items = await apartmentsApi.list(params)
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async fetchOne(id) {
      this.loading = true
      this.error = null
      this.current = null
      try {
        this.current = await apartmentsApi.get(id)
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async create(payload) {
      const created = await apartmentsApi.create(payload)
      this.items.unshift(created)
      return created
    },

    async update(id, payload) {
      const updated = await apartmentsApi.update(id, payload)
      this.current = updated
      const i = this.items.findIndex((a) => a.id === id)
      if (i !== -1) this.items[i] = updated
      return updated
    },

    async remove(id) {
      await apartmentsApi.remove(id)
      this.items = this.items.filter((a) => a.id !== id)
    },
  },
})
