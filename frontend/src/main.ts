import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/global.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
// ElementPlus components are auto-imported by unplugin-vue-components

app.mount('#app')
