<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const user = computed(() => auth.currentUser)

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="navbar">
    <div class="navbar-inner">
      <RouterLink to="/apartments" class="brand">🏠 RentalHub</RouterLink>
      <nav>
        <RouterLink v-if="auth.isAuthenticated" to="/dashboard">Dashboard</RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/my-apartments">My Apartments</RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/my-reservations">My Reservations</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin">Admin</RouterLink>
      </nav>
      <span class="spacer" />
      <template v-if="auth.isAuthenticated">
        <span class="muted">{{ user?.username }}</span>
        <span class="badge" :class="user?.role">{{ user?.role }}</span>
        <button class="btn secondary sm" @click="logout">Log out</button>
      </template>
      <template v-else>
        <RouterLink to="/login" class="btn secondary sm">Log in</RouterLink>
        <RouterLink to="/register" class="btn sm">Sign up</RouterLink>
      </template>
    </div>
  </header>
</template>
