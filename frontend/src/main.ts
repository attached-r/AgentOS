import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { setupRouterGuard } from './router/guard'
import './style.css'

const app = createApp(App)

// Pinia 状态管理
const pinia = createPinia()
app.use(pinia)

// 路由守卫
setupRouterGuard(router)
app.use(router)

// Element Plus UI 库
app.use(ElementPlus)

// 全局注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
