import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, logoutApi } from '@/api/auth'
import type { LoginRequest, UserInfo } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<UserInfo | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(loginForm: LoginRequest) {
    const res = await loginApi(loginForm)
    const data = res.data.data
    token.value = data.tokenValue
    user.value = {
      userId: data.userId,
      username: data.username,
      displayName: data.displayName,
      avatarUrl: data.avatarUrl,
    }
    localStorage.setItem('access_token', data.tokenValue)
  }

  async function logout() {
    try {
      await logoutApi()
    } catch {
      // 即使调用失败也清除本地状态
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('access_token')
    }
  }

  return { token, user, isAuthenticated, login, logout }
})
