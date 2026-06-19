import type { Router } from 'vue-router'

export function setupRouterGuard(router: Router) {
  router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem('access_token')

    if (to.meta.noAuth) {
      // /login 等无需认证的页面
      if (token && to.path === '/login') {
        // 已登录用户访问登录页，重定向到仪表盘
        next('/dashboard')
      } else {
        next()
      }
    } else if (!token) {
      // 未登录访问需要认证的页面
      next('/login')
    } else {
      next()
    }
  })
}
