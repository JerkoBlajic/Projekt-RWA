// =============================================================
// router/index.js - routes + navigation guards
// =============================================================
// meta.public   -> reachable without a session
// meta.adminOnly -> ADMIN role required
// Everything else requires authentication.
// =============================================================

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/apartments' },
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  { path: '/register', name: 'register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
  { path: '/apartments', name: 'apartments', component: () => import('@/views/ApartmentsView.vue'), meta: { public: true } },
  { path: '/apartments/create', name: 'apartment-create', component: () => import('@/views/ApartmentFormView.vue') },
  { path: '/apartments/:id', name: 'apartment-detail', component: () => import('@/views/ApartmentDetailView.vue'), meta: { public: true } },
  { path: '/apartments/:id/edit', name: 'apartment-edit', component: () => import('@/views/ApartmentFormView.vue') },
  { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/my-apartments', name: 'my-apartments', component: () => import('@/views/MyApartmentsView.vue') },
  { path: '/my-reservations', name: 'my-reservations', component: () => import('@/views/MyReservationsView.vue') },
  { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue'), meta: { adminOnly: true } },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue'), meta: { public: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Make sure we have tried to resolve the session at least once.
  if (auth.accessToken && !auth.ready) {
    await auth.fetchCurrentUser()
  }

  if (to.meta.public) return true

  if (!auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.adminOnly && !auth.isAdmin) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
