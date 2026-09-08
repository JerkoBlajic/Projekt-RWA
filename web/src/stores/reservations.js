// =============================================================
// reservations.js - business Pinia store for reservations
// =============================================================

import { defineStore } from 'pinia'
import { reservationsApi } from '@/api/reservations'

export const useReservationsStore = defineStore('reservations', {
  state: () => ({
    items: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchMine() {
      this.loading = true
      this.error = null
      try {
        this.items = await reservationsApi.mine()
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async act(id, action) {
      const updated = await reservationsApi[action](id)
      const i = this.items.findIndex((r) => r.id === id)
      if (i !== -1 && updated) this.items[i] = updated
      return updated
    },

    async remove(id) {
      await reservationsApi.remove(id)
      this.items = this.items.filter((r) => r.id !== id)
    },
  },
})
