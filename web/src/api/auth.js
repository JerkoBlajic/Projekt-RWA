import { api } from './client'

export const authApi = {
  register: (payload) => api.post('/auth/register', payload).then((r) => r.data),
  login: (username, password) =>
    api.post('/auth/login', { username, password }, { skipAuth: true }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
}
