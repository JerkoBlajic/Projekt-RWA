<script setup>
defineProps({ status: { type: String, required: true } })
</script>

<template>
  <span class="badge" :class="status">{{ status }}</span>
</template>
