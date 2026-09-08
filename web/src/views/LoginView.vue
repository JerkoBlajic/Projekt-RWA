<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref(route.query.expired ? 'Your session expired. Please log in again.' : '')
const submitting = ref(false)

async function submit() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = 'Please enter your username and password.'
    return
  }
  submitting.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    router.push(typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard')
  } catch (e) {
    error.value = e.message || 'Login failed.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="panel form-narrow" style="margin: 40px auto">
    <h1 style="margin-bottom: 6px">Log in</h1>
    <p class="muted" style="margin-top: 0">Welcome back to RentalHub.</p>

    <div v-if="error" class="alert error">{{ error }}</div>

    <form @submit.prevent="submit">
      <div class="field">
        <label for="u">Username</label>
        <input id="u" v-model="username" autocomplete="username" />
      </div>
      <div class="field">
        <label for="p">Password</label>
        <input id="p" v-model="password" type="password" autocomplete="current-password" />
      </div>
      <button class="btn" style="width: 100%" :disabled="submitting">
        {{ submitting ? 'Signing in…' : 'Log in' }}
      </button>
    </form>

    <p class="muted" style="margin-top: 16px; text-align: center">
      No account? <RouterLink to="/register">Create one</RouterLink>
    </p>
  </div>
</template>
