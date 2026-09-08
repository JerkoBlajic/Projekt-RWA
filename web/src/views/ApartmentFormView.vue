<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apartmentsApi } from '@/api/apartments'
import { amenitiesApi } from '@/api/admin'

const route = useRoute()
const router = useRouter()
const editId = computed(() => route.params.id)
const isEdit = computed(() => !!editId.value)

const MAX_IMAGE_CHARS = 3_000_000 // must match the backend cap

const form = reactive({
  title: '', image: '', description: '', address: '', city: '',
  price_per_night: '', max_guests: 2, bedrooms: 1, bathrooms: 1,
  area_sqm: '', amenity_ids: [],
})
const errors = reactive({})
const serverError = ref('')
const amenities = ref([])
const loading = ref(true)
const saving = ref(false)
const imageBusy = ref(false)

// ---- client-side image downscaling -----------------------
// The DB stores the picture as a base64 data URI, so we shrink it in the
// browser first (max 1280px, JPEG) to keep it small.
function downscale(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      const max = 1280
      let { width, height } = img
      if (width > max || height > max) {
        const s = max / Math.max(width, height)
        width = Math.round(width * s)
        height = Math.round(height * s)
      }
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      canvas.getContext('2d').drawImage(img, 0, 0, width, height)
      let quality = 0.72
      let out = canvas.toDataURL('image/jpeg', quality)
      while (out.length > MAX_IMAGE_CHARS && quality > 0.4) {
        quality -= 0.1
        out = canvas.toDataURL('image/jpeg', quality)
      }
      resolve(out)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('That file is not a readable image.'))
    }
    img.src = url
  })
}

async function onFile(e) {
  const file = e.target.files?.[0]
  e.target.value = '' // allow re-picking the same file
  if (!file) return
  errors.image = ''
  if (!file.type.startsWith('image/')) {
    errors.image = 'Please choose an image file.'
    return
  }
  imageBusy.value = true
  try {
    const dataUri = await downscale(file)
    if (dataUri.length > MAX_IMAGE_CHARS) {
      errors.image = 'Image is still too large after compression — try a smaller one.'
      return
    }
    form.image = dataUri
  } catch (err) {
    errors.image = err.message
  } finally {
    imageBusy.value = false
  }
}

function clearImage() {
  form.image = ''
  errors.image = ''
}

// ---- validation -----------------------------------------
function validate() {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (form.title.trim().length < 3) errors.title = 'At least 3 characters.'
  if (form.address.trim().length < 3) errors.address = 'Required.'
  if (form.city.trim().length < 2) errors.city = 'Required.'
  if (!(Number(form.price_per_night) > 0)) errors.price_per_night = 'Must be greater than 0.'
  if (!(Number(form.max_guests) > 0)) errors.max_guests = 'Must be greater than 0.'
  if (Number(form.bedrooms) < 0) errors.bedrooms = 'Cannot be negative.'
  if (Number(form.bathrooms) < 0) errors.bathrooms = 'Cannot be negative.'
  if (form.area_sqm !== '' && !(Number(form.area_sqm) > 0))
    errors.area_sqm = 'Must be greater than 0.'
  const img = form.image.trim()
  if (img && !/^(https?:\/\/|data:image\/)/.test(img))
    errors.image = 'Enter a valid URL or upload a file.'
  if (img.length > MAX_IMAGE_CHARS) errors.image = 'Image is too large.'
  return Object.keys(errors).length === 0
}

async function load() {
  loading.value = true
  try {
    amenities.value = await amenitiesApi.list()
    if (isEdit.value) {
      const a = await apartmentsApi.get(editId.value)
      Object.assign(form, {
        title: a.title, image: a.image ?? '', description: a.description ?? '',
        address: a.address, city: a.city, price_per_night: a.price_per_night,
        max_guests: a.max_guests, bedrooms: a.bedrooms, bathrooms: a.bathrooms,
        area_sqm: a.area_sqm ?? '',
        amenity_ids: a.amenities.map((x) => x.id),
      })
    }
  } catch (e) {
    serverError.value = e.message
  } finally {
    loading.value = false
  }
}

async function submit() {
  serverError.value = ''
  if (!validate()) return
  saving.value = true
  const payload = {
    ...form,
    image: form.image.trim() || null,
    price_per_night: Number(form.price_per_night),
    max_guests: Number(form.max_guests),
    bedrooms: Number(form.bedrooms),
    bathrooms: Number(form.bathrooms),
    area_sqm: form.area_sqm === '' ? null : Number(form.area_sqm),
  }
  try {
    const saved = isEdit.value
      ? await apartmentsApi.update(editId.value, payload)
      : await apartmentsApi.create(payload)
    router.push(`/apartments/${saved.id}`)
  } catch (e) {
    serverError.value = e.message
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="panel form-narrow" style="margin: 0 auto">
    <h1>{{ isEdit ? 'Edit apartment' : 'List a new apartment' }}</h1>

    <div v-if="loading" class="state"><div class="spinner" />Loading…</div>

    <form v-else @submit.prevent="submit" novalidate>
      <div v-if="serverError" class="alert error">{{ serverError }}</div>

      <div class="field">
        <label>Title</label>
        <input v-model="form.title" />
        <div v-if="errors.title" class="err">{{ errors.title }}</div>
      </div>

      <div class="field">
        <label>Photo</label>
        <div v-if="form.image" style="margin-bottom: 8px">
          <img
            :src="form.image"
            alt="preview"
            style="width: 100%; height: 180px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border)"
          />
          <button type="button" class="btn secondary sm" style="margin-top: 6px" @click="clearImage">
            Remove photo
          </button>
        </div>
        <input type="file" accept="image/*" :disabled="imageBusy" @change="onFile" />
        <div class="hint">
          {{ imageBusy ? 'Processing image…' : 'Upload from your computer (resized automatically), or paste a URL below.' }}
        </div>
        <input
          v-model="form.image"
          placeholder="https://…"
          style="margin-top: 6px"
          v-if="!form.image.startsWith('data:')"
        />
        <div v-if="errors.image" class="err">{{ errors.image }}</div>
      </div>

      <div class="field">
        <label>Description</label>
        <textarea v-model="form.description" rows="4" />
      </div>
      <div class="row">
        <div class="field">
          <label>Address</label>
          <input v-model="form.address" />
          <div v-if="errors.address" class="err">{{ errors.address }}</div>
        </div>
        <div class="field">
          <label>City</label>
          <input v-model="form.city" />
          <div v-if="errors.city" class="err">{{ errors.city }}</div>
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label>Price / night (€)</label>
          <input v-model="form.price_per_night" type="number" min="1" step="0.01" />
          <div v-if="errors.price_per_night" class="err">{{ errors.price_per_night }}</div>
        </div>
        <div class="field">
          <label>Max guests</label>
          <input v-model="form.max_guests" type="number" min="1" />
          <div v-if="errors.max_guests" class="err">{{ errors.max_guests }}</div>
        </div>
      </div>
      <div class="row">
        <div class="field">
          <label>Bedrooms</label>
          <input v-model="form.bedrooms" type="number" min="0" />
          <div v-if="errors.bedrooms" class="err">{{ errors.bedrooms }}</div>
        </div>
        <div class="field">
          <label>Bathrooms</label>
          <input v-model="form.bathrooms" type="number" min="0" />
          <div v-if="errors.bathrooms" class="err">{{ errors.bathrooms }}</div>
        </div>
        <div class="field">
          <label>Area (m²)</label>
          <input v-model="form.area_sqm" type="number" min="1" placeholder="optional" />
          <div v-if="errors.area_sqm" class="err">{{ errors.area_sqm }}</div>
        </div>
      </div>
      <div class="field">
        <label>Amenities</label>
        <div class="chips">
          <label v-for="am in amenities" :key="am.id" class="chip" style="cursor: pointer">
            <input type="checkbox" :value="am.id" v-model="form.amenity_ids" style="width: auto; margin-right: 4px" />
            {{ am.name }}
          </label>
        </div>
      </div>

      <button class="btn" style="width: 100%" :disabled="saving || imageBusy">
        {{ saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create apartment' }}
      </button>
    </form>
  </div>
</template>
