<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ username: '', email: '', password: '', confirm: '' })
const errors = reactive({})
const serverError = ref('')
const submitting = ref(false)

const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validate() {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (form.username.trim().length < 3) errors.username = 'At least 3 characters.'
  else if (!/^[A-Za-z0-9_.-]+$/.test(form.username)) errors.username = 'Letters, digits, . _ - only.'
  if (!emailRe.test(form.email)) errors.email = 'Enter a valid email address.'
  if (form.password.length < 8) errors.password = 'At least 8 characters.'
  if (form.confirm !== form.password) errors.confirm = 'Passwords do not match.'
  return Object.keys(errors).length === 0
}

async function submit() {
  serverError.value = ''
  if (!validate()) return
  submitting.value = true
  try {
    await auth.register({
      username: form.username.trim(),
      email: form.email.trim(),
      password: form.password,
    })
    router.push('/dashboard')
  } catch (e) {
    serverError.value = e.message || 'Registration failed.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="panel form-narrow" style="margin: 40px auto">
    <h1 style="margin-bottom: 6px">Create your account</h1>
    <p class="muted" style="margin-top: 0">One account to book stays and list your own place.</p>

    <div v-if="serverError" class="alert error">{{ serverError }}</div>

    <form @submit.prevent="submit" novalidate>
      <div class="field">
        <label for="u">Username</label>
        <input id="u" v-model="form.username" />
        <div v-if="errors.username" class="err">{{ errors.username }}</div>
      </div>
      <div class="field">
        <label for="e">Email</label>
        <input id="e" v-model="form.email" type="email" />
        <div v-if="errors.email" class="err">{{ errors.email }}</div>
      </div>
      <div class="field">
        <label for="p">Password</label>
        <input id="p" v-model="form.password" type="password" />
        <div v-if="errors.password" class="err">{{ errors.password }}</div>
      </div>
      <div class="field">
        <label for="c">Confirm password</label>
        <input id="c" v-model="form.confirm" type="password" />
        <div v-if="errors.confirm" class="err">{{ errors.confirm }}</div>
      </div>
      <button class="btn" style="width: 100%" :disabled="submitting">
        {{ submitting ? 'Creating…' : 'Sign up' }}
      </button>
    </form>

    <p class="muted" style="margin-top: 16px; text-align: center">
      Already registered? <RouterLink to="/login">Log in</RouterLink>
    </p>
  </div>
</template>
