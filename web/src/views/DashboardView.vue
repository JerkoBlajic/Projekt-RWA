<script setup>
import { onMounted, ref, computed } from 'vue'
import { apartmentsApi } from '@/api/apartments'
import { reservationsApi } from '@/api/reservations'
import { useAuthStore } from '@/stores/auth'
import AsyncState from '@/components/AsyncState.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const auth = useAuthStore()
const loading = ref(true)
const error = ref(null)
const apartments = ref([])
const reservations = ref([])

const asGuest = computed(() =>
  reservations.value.filter((r) => r.guest_id === auth.currentUser?.id),
)
const asHost = computed(() =>
  reservations.value.filter((r) => r.guest_id !== auth.currentUser?.id),
)
const pendingForMe = computed(() => asHost.value.filter((r) => r.status === 'PENDING').length)

async function load() {
  loading.value = true
  error.value = null
  try {
    ;[apartments.value, reservations.value] = await Promise.all([
      apartmentsApi.mine(),
      reservationsApi.mine(),
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <h1>Dashboard</h1>
  <p class="muted">Signed in as <strong>{{ auth.currentUser?.username }}</strong> ({{ auth.currentUser?.role }})</p>

  <AsyncState :loading="loading" :error="error" @retry="load">
    <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin: 20px 0 28px">
      <div class="panel"><p class="muted" style="margin:0">My apartments</p><p style="font-size:28px;font-weight:700;margin:4px 0 0">{{ apartments.length }}</p></div>
      <div class="panel"><p class="muted" style="margin:0">My trips</p><p style="font-size:28px;font-weight:700;margin:4px 0 0">{{ asGuest.length }}</p></div>
      <div class="panel"><p class="muted" style="margin:0">Requests to review</p><p style="font-size:28px;font-weight:700;margin:4px 0 0">{{ pendingForMe }}</p></div>
    </div>

    <div class="title-row"><h2>My apartments</h2><RouterLink to="/apartments/create" class="btn sm">+ New</RouterLink></div>
    <AsyncState :loading="false" :error="null" :empty="apartments.length === 0" empty-text="You haven't listed any apartments yet.">
      <div class="grid">
        <div v-for="a in apartments" :key="a.id" class="card">
          <div class="body">
            <h2 style="margin:0 0 4px">{{ a.title }}</h2>
            <p class="muted" style="margin:0 0 8px">{{ a.city }} · €{{ Number(a.price_per_night).toFixed(2) }}/night</p>
            <RouterLink :to="`/apartments/${a.id}`" class="btn secondary sm">Manage</RouterLink>
          </div>
        </div>
      </div>
    </AsyncState>

    <h2 style="margin-top: 28px">Latest reservation activity</h2>
    <AsyncState :loading="false" :error="null" :empty="reservations.length === 0" empty-text="No reservation activity yet.">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Apartment</th><th>Dates</th><th>Role</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="r in reservations.slice(0, 8)" :key="r.id">
              <td>{{ r.apartment?.title ?? '#' + r.apartment_id }}</td>
              <td>{{ r.check_in }} → {{ r.check_out }}</td>
              <td>{{ r.guest_id === auth.currentUser?.id ? 'Guest' : 'Host' }}</td>
              <td><StatusBadge :status="r.status" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </AsyncState>
  </AsyncState>
</template>
