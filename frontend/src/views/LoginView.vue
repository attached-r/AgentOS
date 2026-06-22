<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e: any) {
    ElMessage.error(e.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <!-- 左侧品牌展示 -->
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-badge">v2.0</div>
        <h1 class="brand-title">Agent<span class="brand-accent">OS</span></h1>
        <p class="brand-subtitle">智能体操作系统</p>
        <p class="brand-desc">
          构建、部署和管理您的 AI Agent<br>
          集成 MCP 工具链与 RAG 知识库
        </p>
        <div class="brand-features">
          <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <span>ReAct Agent</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🔧</span>
            <span>MCP 工具生态</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📚</span>
            <span>RAG 知识库</span>
          </div>
        </div>
      </div>
      <!-- 背景装饰 -->
      <div class="brand-glow glow-1"></div>
      <div class="brand-glow glow-2"></div>
    </div>
    <!-- 右侧登录表单 -->
    <div class="login-form-wrap">
      <el-card class="login-card" shadow="never">
        <div class="login-header">
          <h2>欢迎回来</h2>
          <p class="login-subtitle">请登录您的账号</p>
        </div>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @keyup.enter="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="'👤'"
            />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="请输入密码"
              size="large"
              :prefix-icon="'🔒'"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              @click="handleLogin"
              style="width: 100%"
              size="large"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  background: #f7f8fa;
}

/* === 左侧品牌区 === */
.login-brand {
  flex: 1;
  background: linear-gradient(135deg, #0f1419 0%, #16202c 50%, #1a2d42 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.brand-content {
  position: relative;
  z-index: 1;
  padding: 40px;
}
.brand-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 20px;
  border: 1px solid rgba(64, 158, 255, 0.2);
}
.brand-title {
  font-size: 48px;
  font-weight: 800;
  color: #fff;
  margin: 0 0 12px;
  letter-spacing: 1px;
}
.brand-accent {
  color: #409eff;
}
.brand-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 24px;
  font-weight: 400;
}
.brand-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.4);
  line-height: 1.7;
  margin-bottom: 36px;
}
.brand-features {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
}
.feature-icon {
  font-size: 20px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

/* 装饰光晕 */
.brand-glow {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.glow-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.08), transparent 70%);
  top: -150px;
  right: -100px;
}
.glow-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.06), transparent 70%);
  bottom: -100px;
  left: -80px;
}

/* === 右侧表单区 === */
.login-form-wrap {
  width: 440px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  flex-shrink: 0;
}
.login-card {
  width: 100%;
  padding: 16px 8px 8px;
  border: none !important;
  box-shadow: none !important;
}
.login-card:hover {
  box-shadow: none !important;
}
.login-header {
  margin-bottom: 32px;
}
.login-header h2 {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}
.login-subtitle {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--color-text-secondary);
  padding-bottom: 6px;
}
:deep(.el-input__prefix) {
  font-size: 16px;
  display: flex;
  align-items: center;
  margin-right: 4px;
}
</style>
