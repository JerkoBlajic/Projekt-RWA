<script setup>
import { onMounted, ref } from 'vue'
import { apartmentsApi } from '@/api/apartments'
import AsyncState from '@/components/AsyncState.vue'

const items = ref([])
const loading = ref(true)
const error = ref(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    items.value = await apartmentsApi.mine()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function remove(id) {
  if (!confirm('Delete this apartment?')) return
  try {
    await apartmentsApi.remove(id)
    items.value = items.value.filter((a) => a.id !== id)
  } catch (e) {
    alert(e.message)
  }
}

onMounted(load)
</script>

<template>
  <div class="title-row">
    <h1>My apartments</h1>
    <RouterLink to="/apartments/create" class="btn">+ List your apartment</RouterLink>
  </div>

  <AsyncState
    :loading="loading"
    :error="error"
    :empty="!loading && !error && items.length === 0"
    empty-text="You don't have any apartments yet."
    @retry="load"
  >
    <div class="table-wrap">
      <table>
        <thead><tr><th>Title</th><th>City</th><th>Price</th><th>Guests</th><th></th></tr></thead>
        <tbody>
          <tr v-for="a in items" :key="a.id">
            <td><RouterLink :to="`/apartments/${a.id}`">{{ a.title }}</RouterLink></td>
            <td>{{ a.city }}</td>
            <td>€{{ Number(a.price_per_night).toFixed(2) }}</td>
            <td>{{ a.max_guests }}</td>
            <td style="display: flex; gap: 6px; justify-content: flex-end">
              <RouterLink :to="`/apartments/${a.id}/edit`" class="btn secondary sm">Edit</RouterLink>
              <button class="btn danger sm" @click="remove(a.id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </AsyncState>
</template>
