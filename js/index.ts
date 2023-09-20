import { createApp } from 'vue'
import FloatingVue from 'floating-vue'
import 'floating-vue/dist/style.css'
import { VTooltip } from 'floating-vue'

import App from './App.vue'
FloatingVue.options.themes.tooltip.disabled = window.innerWidth <= 768
FloatingVue.options.themes.tooltip.delay.show = 100
const app = createApp(App)
app.use(FloatingVue)

app.mount('#app')
