import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'
import { useAuthStore } from './stores/auth'

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)

  // Resolve the session before the router mounts so guards see the truth.
  const auth = useAuthStore(pinia)
  if (auth.accessToken) {
    await auth.fetchCurrentUser()
  } else {
    auth.ready = true
  }

  app.use(router)
  app.mount('#app')
}

bootstrap()
