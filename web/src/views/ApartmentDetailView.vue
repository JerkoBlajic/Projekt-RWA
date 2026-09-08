<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apartmentsApi } from '@/api/apartments'
import { reservationsApi } from '@/api/reservations'
import { useAuthStore } from '@/stores/auth'
import AsyncState from '@/components/AsyncState.vue'
import StatusBadge from '@/components/StatusBadge.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const apartment = ref(null)
const loading = ref(true)
const error = ref(null)

const reservations = ref([])
const resLoading = ref(false)

const busyRanges = ref([]) // [{ check_in, check_out, status }]

const isOwner = computed(
  () => apartment.value && auth.currentUser?.id === apartment.value.owner_id,
)
const canManage = computed(() => isOwner.value || auth.isAdmin)

const booking = reactive({ check_in: '', check_out: '', guests_count: 1 })
const bookingErrors = reactive({})
const bookingServerError = ref('')
const bookingOk = ref('')
const bookingBusy = ref(false)

// ---- availability helpers ---------------------------------

// Local calendar date as YYYY-MM-DD (avoids UTC off-by-one from toISOString).
function ymd(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const today = ymd(new Date())

// A day is booked if some active range covers it: check_in <= day < check_out.
function isBooked(iso) {
  return busyRanges.value.some((r) => iso >= r.check_in && iso < r.check_out)
}

// True if any night in [ci, co) is already taken.
function rangeHasConflict(ci, co) {
  if (!ci || !co || co <= ci) return false
  const cur = new Date(ci + 'T00:00:00')
  const end = new Date(co + 'T00:00:00')
  while (cur < end) {
    if (isBooked(ymd(cur))) return true
    cur.setDate(cur.getDate() + 1)
  }
  return false
}

// Calendar grid: today .. +7 weeks, aligned to weekday columns.
const calendar = computed(() => {
  const start = new Date(today + 'T00:00:00')
  const lead = start.getDay() // 0 = Sunday
  const cells = []
  for (let i = 0; i < lead; i++) cells.push(null)
  for (let i = 0; i < 49; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    const iso = ymd(d)
    cells.push({
      iso,
      day: d.getDate(),
      firstOfMonth: d.getDate() === 1 || i === 0,
      monthLabel: d.toLocaleDateString(undefined, { month: 'short' }),
      booked: isBooked(iso),
      inSelection:
        booking.check_in &&
        booking.check_out &&
        iso >= booking.check_in &&
        iso < booking.check_out,
      isStart: iso === booking.check_in,
    })
  }
  return cells
})

const dayNames = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

function pickDay(cell) {
  if (!cell || cell.booked) return
  bookingErrors.range = ''
  // start a new selection, or extend it
  if (!booking.check_in || booking.check_out || cell.iso <= booking.check_in) {
    booking.check_in = cell.iso
    booking.check_out = ''
    return
  }
  if (rangeHasConflict(booking.check_in, cell.iso)) {
    bookingErrors.range = 'Those nights include a date that is already booked.'
    return
  }
  booking.check_out = cell.iso
}

// ---- load -------------------------------------------------

async function load() {
  loading.value = true
  error.value = null
  try {
    apartment.value = await apartmentsApi.get(route.params.id)
    busyRanges.value = await apartmentsApi.availability(apartment.value.id)
    if (canManage.value) loadReservations()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadReservations() {
  resLoading.value = true
  try {
    reservations.value = await apartmentsApi.reservations(apartment.value.id)
  } catch {
    reservations.value = []
  } finally {
    resLoading.value = false
  }
}

function fmt(iso) {
  return new Date(iso + 'T00:00:00').toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

// ---- booking ---------------------------------------------

function validateBooking() {
  Object.keys(bookingErrors).forEach((k) => delete bookingErrors[k])
  if (!booking.check_in) bookingErrors.check_in = 'Pick a check-in date.'
  if (!booking.check_out) bookingErrors.check_out = 'Pick a check-out date.'
  if (booking.check_in && booking.check_out && booking.check_out <= booking.check_in)
    bookingErrors.check_out = 'Check-out must be after check-in.'
  if (booking.check_in && booking.check_in < today)
    bookingErrors.check_in = 'Check-in cannot be in the past.'
  if (
    booking.check_in &&
    booking.check_out &&
    booking.check_out > booking.check_in &&
    rangeHasConflict(booking.check_in, booking.check_out)
  )
    bookingErrors.range = 'Those dates overlap a booking that is already on the calendar.'
  const g = Number(booking.guests_count)
  if (!g || g < 1) bookingErrors.guests_count = 'At least one guest.'
  else if (apartment.value && g > apartment.value.max_guests)
    bookingErrors.guests_count = `This place holds at most ${apartment.value.max_guests} guests.`
  return Object.keys(bookingErrors).length === 0
}

async function submitBooking() {
  bookingServerError.value = ''
  bookingOk.value = ''
  if (!auth.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  if (!validateBooking()) return
  bookingBusy.value = true
  try {
    await apartmentsApi.book(apartment.value.id, {
      check_in: booking.check_in,
      check_out: booking.check_out,
      guests_count: Number(booking.guests_count),
    })
    bookingOk.value = 'Reservation requested! Track it under "My Reservations".'
    booking.check_in = booking.check_out = ''
    booking.guests_count = 1
    busyRanges.value = await apartmentsApi.availability(apartment.value.id)
  } catch (e) {
    bookingServerError.value = e.message
  } finally {
    bookingBusy.value = false
  }
}

async function act(id, action) {
  try {
    await reservationsApi[action](id)
    await loadReservations()
    busyRanges.value = await apartmentsApi.availability(apartment.value.id)
  } catch (e) {
    alert(e.message)
  }
}

async function removeApartment() {
  if (!confirm('Delete this apartment? This cannot be undone.')) return
  try {
    await apartmentsApi.remove(apartment.value.id)
    router.push('/my-apartments')
  } catch (e) {
    alert(e.message)
  }
}

onMounted(load)
</script>

<template>
  <AsyncState :loading="loading" :error="error" @retry="load">
    <template v-if="apartment">
      <div class="title-row">
        <h1>{{ apartment.title }}</h1>
        <div v-if="isOwner" style="display: flex; gap: 8px">
          <RouterLink :to="`/apartments/${apartment.id}/edit`" class="btn secondary sm">Edit</RouterLink>
          <button class="btn danger sm" @click="removeApartment">Delete</button>
        </div>
      </div>

      <img
        v-if="apartment.image"
        :src="apartment.image"
        alt=""
        style="width: 100%; max-height: 340px; object-fit: cover; border-radius: var(--radius); margin-bottom: 20px"
      />

      <div class="detail-grid">
        <div>
          <div class="meta-list" style="margin-bottom: 14px">
            <span>📍 {{ apartment.address }}, {{ apartment.city }}</span>
            <span>👥 {{ apartment.max_guests }} guests</span>
            <span>🛏 {{ apartment.bedrooms }} bd</span>
            <span>🛁 {{ apartment.bathrooms }} ba</span>
            <span v-if="apartment.area_sqm">📐 {{ apartment.area_sqm }} m²</span>
          </div>
          <p>{{ apartment.description || 'No description provided.' }}</p>
          <div class="chips" v-if="apartment.amenities?.length" style="margin-top: 14px">
            <span class="chip" v-for="a in apartment.amenities" :key="a.id">{{ a.name }}</span>
          </div>

          <!-- Availability calendar -->
          <section style="margin-top: 24px">
            <h2 style="margin-bottom: 4px">Availability</h2>
            <p class="muted" style="margin-top: 0; font-size: 13px">
              Greyed days are already booked.
              <span v-if="!isOwner">Click a free day for check-in, then another for check-out.</span>
            </p>

            <div class="cal">
              <div class="cal-dow" v-for="d in dayNames" :key="d">{{ d }}</div>
              <template v-for="(c, i) in calendar" :key="i">
                <div v-if="!c" class="cal-cell empty" />
                <button
                  v-else
                  type="button"
                  class="cal-cell"
                  :class="{
                    booked: c.booked,
                    sel: c.inSelection,
                    start: c.isStart,
                    clickable: !c.booked && !isOwner,
                  }"
                  :disabled="c.booked || isOwner"
                  @click="pickDay(c)"
                >
                  <span v-if="c.firstOfMonth" class="cal-month">{{ c.monthLabel }}</span>
                  {{ c.day }}
                </button>
              </template>
            </div>

            <p v-if="busyRanges.length" class="muted" style="font-size: 13px; margin-top: 10px">
              Booked:
              <span v-for="(r, i) in busyRanges" :key="i">
                {{ fmt(r.check_in) }} – {{ fmt(r.check_out) }}<span v-if="i < busyRanges.length - 1">, </span>
              </span>
            </p>
            <p v-else class="muted" style="font-size: 13px; margin-top: 10px">No bookings yet — all dates are open.</p>
          </section>
        </div>

        <div class="panel">
          <p class="price" style="margin: 0 0 12px">
            €{{ Number(apartment.price_per_night).toFixed(2) }}
            <span class="muted" style="font-weight: 400; font-size: 13px">/ night</span>
          </p>

          <template v-if="isOwner">
            <p class="muted">This is your apartment. Manage its reservations below.</p>
          </template>

          <form v-else @submit.prevent="submitBooking">
            <div v-if="bookingServerError" class="alert error">{{ bookingServerError }}</div>
            <div v-if="bookingOk" class="alert info">{{ bookingOk }}</div>
            <div v-if="bookingErrors.range" class="alert error">{{ bookingErrors.range }}</div>
            <div class="field">
              <label>Check-in</label>
              <input v-model="booking.check_in" type="date" :min="today" />
              <div v-if="bookingErrors.check_in" class="err">{{ bookingErrors.check_in }}</div>
            </div>
            <div class="field">
              <label>Check-out</label>
              <input v-model="booking.check_out" type="date" :min="booking.check_in || today" />
              <div v-if="bookingErrors.check_out" class="err">{{ bookingErrors.check_out }}</div>
            </div>
            <div class="field">
              <label>Guests</label>
              <input v-model="booking.guests_count" type="number" min="1" :max="apartment.max_guests" />
              <div v-if="bookingErrors.guests_count" class="err">{{ bookingErrors.guests_count }}</div>
            </div>
            <button class="btn" style="width: 100%" :disabled="bookingBusy">
              {{ bookingBusy ? 'Requesting…' : 'Request to book' }}
            </button>
          </form>
        </div>
      </div>

      <section v-if="canManage" style="margin-top: 32px">
        <h2>Reservations for this apartment</h2>
        <AsyncState
          :loading="resLoading"
          :error="null"
          :empty="!resLoading && reservations.length === 0"
          empty-text="No reservations yet."
        >
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Guest</th><th>Dates</th><th>People</th><th>Status</th><th></th></tr>
              </thead>
              <tbody>
                <tr v-for="r in reservations" :key="r.id">
                  <td>{{ r.guest?.username ?? '#' + r.guest_id }}</td>
                  <td>{{ r.check_in }} → {{ r.check_out }}</td>
                  <td>{{ r.guests_count }}</td>
                  <td><StatusBadge :status="r.status" /></td>
                  <td style="display: flex; gap: 6px; justify-content: flex-end">
                    <button v-if="r.status === 'PENDING'" class="btn success sm" @click="act(r.id, 'approve')">Approve</button>
                    <button v-if="r.status === 'PENDING'" class="btn danger sm" @click="act(r.id, 'reject')">Reject</button>
                    <button v-if="r.status === 'APPROVED'" class="btn secondary sm" @click="act(r.id, 'complete')">Mark completed</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </AsyncState>
      </section>
    </template>
  </AsyncState>
</template>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  align-items: start;
}
@media (max-width: 780px) {
  .detail-grid { grid-template-columns: 1fr; }
}

.cal {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  max-width: 360px;
}
.cal-dow {
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  padding-bottom: 2px;
}
.cal-cell {
  position: relative;
  aspect-ratio: 1 / 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  font: inherit;
  font-size: 13px;
  color: var(--text);
  padding: 0;
}
.cal-cell.empty { border: none; background: transparent; }
.cal-cell.clickable { cursor: pointer; }
.cal-cell.clickable:hover { border-color: var(--primary); }
.cal-cell.booked {
  background: #eceef1;
  color: #a2a9b3;
  text-decoration: line-through;
  cursor: not-allowed;
}
.cal-cell.sel { background: #dbe6ff; border-color: var(--primary); }
.cal-cell.start { background: var(--primary); color: #fff; border-color: var(--primary); }
.cal-month {
  position: absolute;
  top: -14px;
  left: 0;
  font-size: 10px;
  font-weight: 700;
  color: var(--muted);
}
</style>
