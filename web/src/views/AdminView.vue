<script setup>
import { onMounted, ref } from 'vue'
import { adminApi } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import AsyncState from '@/components/AsyncState.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const auth = useAuthStore()
const tab = ref('users')
const loading = ref(true)
const error = ref(null)
const users = ref([])
const apartments = ref([])
const reservations = ref([])

async function load() {
  loading.value = true
  error.value = null
  try {
    ;[users.value, apartments.value, reservations.value] = await Promise.all([
      adminApi.users(),
      adminApi.apartments(),
      adminApi.reservations(),
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function toggleRole(u) {
  const role = u.role === 'ADMIN' ? 'USER' : 'ADMIN'
  try {
    const updated = await adminApi.setRole(u.id, role)
    Object.assign(u, updated)
  } catch (e) {
    alert(e.message)
  }
}

async function removeUser(u) {
  if (!confirm(`Delete user "${u.username}"? Their apartments and reservations go too.`)) return
  try {
    await adminApi.deleteUser(u.id)
    users.value = users.value.filter((x) => x.id !== u.id)
  } catch (e) {
    alert(e.message)
  }
}

onMounted(load)
</script>

<template>
  <h1>Admin dashboard</h1>

  <div style="display: flex; gap: 8px; margin: 16px 0 20px">
    <button v-for="t in ['users', 'apartments', 'reservations']" :key="t"
      class="btn sm" :class="{ secondary: tab !== t }" @click="tab = t">
      {{ t }} ({{ t === 'users' ? users.length : t === 'apartments' ? apartments.length : reservations.length }})
    </button>
  </div>

  <AsyncState :loading="loading" :error="error" @retry="load">
    <div v-show="tab === 'users'" class="table-wrap">
      <table>
        <thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th></th></tr></thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email }}</td>
            <td><span class="badge" :class="u.role">{{ u.role }}</span></td>
            <td style="display: flex; gap: 6px; justify-content: flex-end">
              <button v-if="u.id !== auth.currentUser?.id" class="btn secondary sm" @click="toggleRole(u)">
                Make {{ u.role === 'ADMIN' ? 'USER' : 'ADMIN' }}
              </button>
              <button v-if="u.id !== auth.currentUser?.id" class="btn danger sm" @click="removeUser(u)">Delete</button>
              <span v-else class="muted">you</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="tab === 'apartments'" class="table-wrap">
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>City</th><th>Owner</th><th>Price</th></tr></thead>
        <tbody>
          <tr v-for="a in apartments" :key="a.id">
            <td>{{ a.id }}</td>
            <td><RouterLink :to="`/apartments/${a.id}`">{{ a.title }}</RouterLink></td>
            <td>{{ a.city }}</td>
            <td>{{ a.owner?.username ?? '#' + a.owner_id }}</td>
            <td>€{{ Number(a.price_per_night).toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="tab === 'reservations'" class="table-wrap">
      <table>
        <thead><tr><th>ID</th><th>Apartment</th><th>Guest</th><th>Dates</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="r in reservations" :key="r.id">
            <td>{{ r.id }}</td>
            <td>{{ r.apartment?.title ?? '#' + r.apartment_id }}</td>
            <td>{{ r.guest?.username ?? '#' + r.guest_id }}</td>
            <td>{{ r.check_in }} → {{ r.check_out }}</td>
            <td><StatusBadge :status="r.status" /></td>
          </tr>
        </tbody>
      </table>
    </div>
  </AsyncState>
</template>
