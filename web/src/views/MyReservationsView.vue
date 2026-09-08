<script setup>
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useReservationsStore } from '@/stores/reservations'
import { useAuthStore } from '@/stores/auth'
import AsyncState from '@/components/AsyncState.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const store = useReservationsStore()
const auth = useAuthStore()
const { items, loading, error } = storeToRefs(store)

const trips = computed(() => items.value.filter((r) => r.guest_id === auth.currentUser?.id))
const hosting = computed(() => items.value.filter((r) => r.guest_id !== auth.currentUser?.id))

function load() {
  store.fetchMine()
}

async function run(id, action) {
  try {
    await store.act(id, action)
  } catch (e) {
    alert(e.message)
  }
}

async function drop(id) {
  if (!confirm('Delete this reservation?')) return
  try {
    await store.remove(id)
  } catch (e) {
    alert(e.message)
  }
}

onMounted(load)
</script>

<template>
  <h1>My reservations</h1>

  <AsyncState
    :loading="loading"
    :error="error"
    :empty="!loading && !error && items.length === 0"
    empty-text="You have no reservations yet. Browse apartments to book your first stay."
    @retry="load"
  >
    <section>
      <h2>Trips I booked</h2>
      <p v-if="trips.length === 0" class="muted">No trips booked.</p>
      <div v-else class="table-wrap">
        <table>
          <thead><tr><th>Apartment</th><th>Dates</th><th>Guests</th><th>Status</th><th></th></tr></thead>
          <tbody>
            <tr v-for="r in trips" :key="r.id">
              <td>{{ r.apartment?.title ?? '#' + r.apartment_id }}</td>
              <td>{{ r.check_in }} → {{ r.check_out }}</td>
              <td>{{ r.guests_count }}</td>
              <td><StatusBadge :status="r.status" /></td>
              <td style="display: flex; gap: 6px; justify-content: flex-end">
                <button v-if="['PENDING', 'APPROVED'].includes(r.status)" class="btn secondary sm" @click="run(r.id, 'cancel')">Cancel</button>
                <button v-else class="btn danger sm" @click="drop(r.id)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section style="margin-top: 28px">
      <h2>Requests for my apartments</h2>
      <p v-if="hosting.length === 0" class="muted">No incoming requests.</p>
      <div v-else class="table-wrap">
        <table>
          <thead><tr><th>Apartment</th><th>Guest</th><th>Dates</th><th>Status</th><th></th></tr></thead>
          <tbody>
            <tr v-for="r in hosting" :key="r.id">
              <td>{{ r.apartment?.title ?? '#' + r.apartment_id }}</td>
              <td>{{ r.guest?.username ?? '#' + r.guest_id }}</td>
              <td>{{ r.check_in }} → {{ r.check_out }}</td>
              <td><StatusBadge :status="r.status" /></td>
              <td style="display: flex; gap: 6px; justify-content: flex-end">
                <button v-if="r.status === 'PENDING'" class="btn success sm" @click="run(r.id, 'approve')">Approve</button>
                <button v-if="r.status === 'PENDING'" class="btn danger sm" @click="run(r.id, 'reject')">Reject</button>
                <button v-if="r.status === 'APPROVED'" class="btn secondary sm" @click="run(r.id, 'complete')">Complete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </AsyncState>
</template>
