<script setup>
// Wraps the three required UX states: loading / error / empty.
// Renders the default slot only when there is data and no error.
defineProps({
  loading: Boolean,
  error: { type: [String, null], default: null },
  empty: Boolean,
  emptyText: { type: String, default: 'Nothing here yet.' },
})
defineEmits(['retry'])
</script>

<template>
  <div v-if="loading" class="state">
    <div class="spinner" />
    Loading…
  </div>
  <div v-else-if="error" class="state">
    <p class="alert error">{{ error }}</p>
    <button class="btn secondary sm" @click="$emit('retry')">Try again</button>
  </div>
  <div v-else-if="empty" class="state">{{ emptyText }}</div>
  <slot v-else />
</template>
