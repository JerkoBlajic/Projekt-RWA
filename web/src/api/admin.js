import { api } from './client'

export const adminApi = {
  users: () => api.get('/admin/users').then((r) => r.data),
  apartments: () => api.get('/admin/apartments').then((r) => r.data),
  reservations: () => api.get('/admin/reservations').then((r) => r.data),
  setRole: (id, role) => api.patch(`/admin/users/${id}`, { role }).then((r) => r.data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`).then((r) => r.data),
}

export const amenitiesApi = {
  list: () => api.get('/amenities').then((r) => r.data),
}
