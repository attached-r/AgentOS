<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  Odometer,
  Monitor,
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
        <span class="logo-text">AgentOS</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :router="true"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#fff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/agents">
          <el-icon><Monitor /></el-icon>
          <span>Agent 管理</span>
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
.app-sidebar {
  background-color: #001529;
  overflow-y: auto;
}
.sidebar-logo {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.logo-text {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 50px;
}
.header-left {
  display: flex;
  align-items: center;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-name {
  font-size: 14px;
  color: #606266;
}
.app-main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
