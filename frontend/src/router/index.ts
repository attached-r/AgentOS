import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { noAuth: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/LayoutMain.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
      },
      {
        path: 'agents',
        name: 'AgentList',
        component: () => import('@/views/AgentListView.vue'),
      },
      {
        path: 'agents/new',
        name: 'AgentNew',
        component: () => import('@/views/AgentFormView.vue'),
      },
      {
        path: 'agents/:id/edit',
        name: 'AgentEdit',
        component: () => import('@/views/AgentFormView.vue'),
      },
      {
        path: 'conversations',
        name: 'ConversationList',
        component: () => import('@/views/ConversationListView.vue'),
      },
      {
        path: 'conversations/:id',
        name: 'Chat',
        component: () => import('@/views/ChatView.vue'),
      },
      {
        path: 'api-keys',
        name: 'ApiKeys',
        component: () => import('@/views/ApiKeysView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
