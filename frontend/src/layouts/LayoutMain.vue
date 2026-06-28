<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer,
  Monitor,
  Tools,
  Document,
  ChatDotSquare,
  Key,
  SwitchButton,
  Search,
  Expand,
  Fold,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)

const activeMenu = computed(() => route.path)

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

const displayName = computed(() => {
  return authStore.user?.displayName || authStore.user?.username || 'User'
})

const navItems = [
  { path: '/dashboard', icon: Odometer, label: '仪表盘' },
  { path: '/agents', icon: Monitor, label: 'Agent 管理' },
  { path: '/tools', icon: Tools, label: '工具中心' },
  { path: '/knowledge', icon: Document, label: '知识库' },
  { path: '/conversations', icon: ChatDotSquare, label: '对话列表' },
  { path: '/api-keys', icon: Key, label: 'API Key' },
]
</script>

<template>
  <div class="app-shell">
    <!-- ========== 侧栏 ========== -->
    <aside class="app-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- Logo -->
      <div class="sidebar-logo">
        <span class="logo-icon">A</span>
        <span v-show="!sidebarCollapsed" class="logo-text">
          Agent<span class="logo-accent">OS</span>
        </span>
      </div>

      <!-- 搜索（豆包风格快捷入口） -->
      <div v-show="!sidebarCollapsed" class="sidebar-search">
        <el-icon><Search /></el-icon>
        <span class="search-placeholder">快速搜索...</span>
      </div>

      <!-- 导航 -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: activeMenu.startsWith(item.path) }"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span v-show="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- 底部用户 -->
      <div class="sidebar-footer">
        <div class="sidebar-user">
          <div class="user-avatar">{{ displayName.charAt(0).toUpperCase() }}</div>
          <div v-show="!sidebarCollapsed" class="user-info">
            <span class="user-name">{{ displayName }}</span>
          </div>
          <el-tooltip content="退出登录" placement="right">
            <el-button text class="logout-btn" @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <!-- 折叠按钮 -->
      <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
      </button>
    </aside>

    <!-- ========== 主区域 ========== -->
    <div class="app-main-area" :class="{ sidebarCollapsed }">
      <!-- 极简顶栏 -->
      <header class="app-header">
        <div class="header-left">
          <h1 class="page-title">{{ route.meta?.title || '' }}</h1>
        </div>
        <div class="header-right">
          <span class="header-date">{{ new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' }) }}</span>
        </div>
      </header>

      <!-- 内容 -->
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ============================================================
   App Shell — Doubao 风格
   ============================================================ */
.app-shell {
  display: flex;
  height: 100vh;
  background: var(--bg-secondary);
}

/* ============================
   侧栏
   ============================ */
.app-sidebar {
  width: 220px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
  transition: width var(--transition-normal);
  z-index: 10;
}
.app-sidebar.collapsed {
  width: 64px;
}

/* Logo */
.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-subtle);
}
.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--accent), #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  flex-shrink: 0;
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.3px;
  white-space: nowrap;
}
.logo-accent {
  color: var(--accent);
}

/* 搜索快捷入口 */
.sidebar-search {
  margin: 12px 12px 8px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background var(--transition-fast);
  color: var(--text-tertiary);
  font-size: 13px;
}
.sidebar-search:hover {
  background: var(--bg-tertiary);
}
.search-placeholder {
  white-space: nowrap;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 6px 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 450;
  transition: all var(--transition-fast);
  cursor: pointer;
  white-space: nowrap;
}
.nav-item:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}
.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 500;
}
.nav-item .el-icon {
  flex-shrink: 0;
}

/* 底部用户 */
.sidebar-footer {
  padding: 10px 8px;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 4px 4px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.sidebar-user:hover {
  background: var(--bg-secondary);
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.user-info {
  flex: 1;
  min-width: 0;
}
.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}
.logout-btn {
  color: var(--text-tertiary);
  padding: 4px;
  flex-shrink: 0;
}
.logout-btn:hover {
  color: var(--color-danger);
}

/* 折叠按钮 */
.collapse-btn {
  position: absolute;
  right: -14px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-primary);
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-tertiary);
  font-size: 14px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
  z-index: 5;
}
.collapse-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
  box-shadow: var(--shadow-md);
}

/* ============================
   主区域
   ============================ */
.app-main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: margin-left var(--transition-normal);
}

/* 顶栏 */
.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: transparent;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-date {
  font-size: 13px;
  color: var(--text-tertiary);
  font-weight: 400;
}

/* 内容区 */
.app-content {
  flex: 1;
  padding: 0 28px 28px;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
