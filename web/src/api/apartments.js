import { api } from './client'

export const apartmentsApi = {
  list: (params = {}) => api.get('/apartments', { params }).then((r) => r.data),
  get: (id) => api.get(`/apartments/${id}`).then((r) => r.data),
  create: (payload) => api.post('/apartments', payload).then((r) => r.data),
  update: (id, payload) => api.put(`/apartments/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/apartments/${id}`).then((r) => r.data),
  mine: () => api.get('/users/me/apartments').then((r) => r.data),
  reservations: (id) => api.get(`/apartments/${id}/reservations`).then((r) => r.data),
  availability: (id) => api.get(`/apartments/${id}/availability`).then((r) => r.data),
  book: (id, payload) =>
    api.post(`/apartments/${id}/reservations`, payload).then((r) => r.data),
}
