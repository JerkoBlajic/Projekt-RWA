<script setup>
import { onMounted, reactive } from 'vue'
import { storeToRefs } from 'pinia'
import { useApartmentsStore } from '@/stores/apartments'
import { useAuthStore } from '@/stores/auth'
import ApartmentCard from '@/components/ApartmentCard.vue'
import AsyncState from '@/components/AsyncState.vue'

const store = useApartmentsStore()
const auth = useAuthStore()
const { items, loading, error } = storeToRefs(store)

const filters = reactive({ city: '', max_price: '', guests: '' })

function load() {
  const params = {}
  if (filters.city.trim()) params.city = filters.city.trim()
  if (filters.max_price) params.max_price = filters.max_price
  if (filters.guests) params.guests = filters.guests
  store.fetchAll(params)
}

onMounted(load)
</script>

<template>
  <div class="title-row">
    <h1>Browse apartments</h1>
    <RouterLink v-if="auth.isAuthenticated" to="/apartments/create" class="btn">+ List your apartment</RouterLink>
  </div>

  <div class="panel" style="margin-bottom: 24px">
    <form class="row" @submit.prevent="load">
      <div class="field" style="margin: 0">
        <label>City</label>
        <input v-model="filters.city" placeholder="e.g. Split" />
      </div>
      <div class="field" style="margin: 0">
        <label>Max price / night</label>
        <input v-model="filters.max_price" type="number" min="1" />
      </div>
      <div class="field" style="margin: 0">
        <label>Guests</label>
        <input v-model="filters.guests" type="number" min="1" />
      </div>
      <div class="field" style="margin: 0; display: flex; align-items: flex-end">
        <button class="btn secondary" type="submit">Apply filters</button>
      </div>
    </form>
  </div>

  <AsyncState
    :loading="loading"
    :error="error"
    :empty="!loading && !error && items.length === 0"
    empty-text="No apartments match your search."
    @retry="load"
  >
    <div class="grid">
      <ApartmentCard v-for="a in items" :key="a.id" :apartment="a" />
    </div>
  </AsyncState>
</template>
