<script setup>
defineProps({ apartment: { type: Object, required: true } })
const placeholder =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><rect width="100%" height="100%" fill="%23dde1e7"/><text x="50%" y="50%" font-family="sans-serif" font-size="16" fill="%237a828e" text-anchor="middle" dy=".3em">No image</text></svg>',
  )
</script>

<template>
  <RouterLink :to="`/apartments/${apartment.id}`" class="card" style="color: inherit">
    <img :src="apartment.image || placeholder" :alt="apartment.title" @error="(e) => (e.target.src = placeholder)" />
    <div class="body">
      <h2 style="margin: 0 0 4px">{{ apartment.title }}</h2>
      <p class="muted" style="margin: 0 0 10px">{{ apartment.city }} · up to {{ apartment.max_guests }} guests</p>
      <div class="chips" v-if="apartment.amenities?.length">
        <span class="chip" v-for="a in apartment.amenities.slice(0, 3)" :key="a.id">{{ a.name }}</span>
      </div>
      <p class="price" style="margin: 12px 0 0">€{{ Number(apartment.price_per_night).toFixed(2) }} <span class="muted" style="font-weight: 400; font-size: 13px">/ night</span></p>
    </div>
  </RouterLink>
</template>
