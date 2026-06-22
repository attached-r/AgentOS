<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer,
  Monitor,
  Tools,
  Document,
  ChatDotSquare,
  Key,
  SwitchButton,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

const displayName = computed(() => {
  return authStore.user?.displayName || authStore.user?.username || 'User'
})
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" class="app-sidebar">
      <div class="sidebar-logo">
        <span class="logo-text">Agent<span class="logo-accent">OS</span></span>
      </div>
      <div class="sidebar-menu-wrap">
        <el-menu
          :default-active="activeMenu"
          :router="true"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/agents">
            <el-icon><Monitor /></el-icon>
            <span>Agent 管理</span>
          </el-menu-item>
          <el-menu-item index="/tools">
            <el-icon><Tools /></el-icon>
            <span>工具中心</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Document /></el-icon>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/conversations">
            <el-icon><ChatDotSquare /></el-icon>
            <span>对话列表</span>
          </el-menu-item>
          <el-menu-item index="/api-keys">
            <el-icon><Key /></el-icon>
            <span>API Key</span>
          </el-menu-item>
        </el-menu>
      </div>
      <div class="sidebar-footer">
        <div class="sidebar-user-avatar">{{ displayName.charAt(0).toUpperCase() }}</div>
        <span class="sidebar-user-name">{{ displayName }}</span>
      </div>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <span class="page-title">{{ route.meta?.title || '' }}</span>
        </div>
        <div class="header-right">
          <span class="user-name">{{ displayName }}</span>
          <el-button text type="primary" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
/* === 侧栏 — Linear/Notion 混合风格 === */
.app-sidebar {
  background: #0f1419;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
}
.logo-text {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.logo-accent {
  color: #409eff;
}

/* 菜单 */
.sidebar-menu-wrap {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}
:deep(.el-menu) {
  background: transparent !important;
  border-right: none;
}
:deep(.el-menu-item) {
  margin: 2px 10px;
  border-radius: 6px;
  height: 38px;
  line-height: 38px;
  color: rgba(255, 255, 255, 0.55);
  font-size: 14px;
  transition: all 0.12s ease;
  width: auto;
  padding: 0 12px;
}
:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.85);
}
:deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
  font-weight: 500;
}
:deep(.el-menu-item .el-icon) {
  margin-right: 8px;
  font-size: 17px;
  color: inherit;
}

/* 底部用户栏 */
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.sidebar-user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: linear-gradient(135deg, #409eff, #3a8ee6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
.sidebar-user-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* === 顶栏 === */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  padding: 0 24px;
  height: 56px;
  flex-shrink: 0;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-name {
  font-size: 13px;
  color: var(--color-text-muted);
}

/* === 内容区 === */
.app-main {
  background-color: var(--color-bg);
  padding: 24px;
  overflow-y: auto;
}
</style>
