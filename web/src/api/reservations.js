import { api } from './client'

export const reservationsApi = {
  list: () => api.get('/reservations').then((r) => r.data),
  mine: () => api.get('/users/me/reservations').then((r) => r.data),
  get: (id) => api.get(`/reservations/${id}`).then((r) => r.data),
  update: (id, payload) => api.put(`/reservations/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/reservations/${id}`).then((r) => r.data),
  approve: (id) => api.post(`/reservations/${id}/approve`).then((r) => r.data),
  reject: (id) => api.post(`/reservations/${id}/reject`).then((r) => r.data),
  cancel: (id) => api.post(`/reservations/${id}/cancel`).then((r) => r.data),
  complete: (id) => api.post(`/reservations/${id}/complete`).then((r) => r.data),
}
