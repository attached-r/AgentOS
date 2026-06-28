<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const isRegisterMode = ref(false)
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  displayName: '',
})

const rules = computed(() => {
  const base: Record<string, any[]> = {
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, max: 20, message: '用户名长度 3-20 个字符', trigger: 'blur' },
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
    ],
  }
  if (isRegisterMode.value) {
    base.confirmPassword = [
      { required: true, message: '请确认密码', trigger: 'blur' },
      {
        validator: (_rule: any, value: string, callback: Function) => {
          if (value !== form.password) {
            callback(new Error('两次输入的密码不一致'))
          } else {
            callback()
          }
        },
        trigger: 'blur',
      },
    ]
  }
  return base
})

const formTitle = computed(() => isRegisterMode.value ? '创建账号' : '欢迎回来')
const formSubtitle = computed(() => isRegisterMode.value ? '注册一个新账号开始使用' : '登录您的账号继续')
const submitText = computed(() => loading.value ? (isRegisterMode.value ? '注册中...' : '登录中...') : (isRegisterMode.value ? '注册' : '登录'))
const toggleText = computed(() => isRegisterMode.value ? '已有账号？去登录' : '没有账号？去注册')

function toggleMode() {
  isRegisterMode.value = !isRegisterMode.value
  formRef.value?.resetFields()
}

async function handleSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isRegisterMode.value) {
      await authStore.register({
        username: form.username,
        password: form.password,
        displayName: form.displayName || undefined,
      })
      ElMessage.success('注册成功')
    } else {
      await authStore.login({
        username: form.username,
        password: form.password,
      })
      ElMessage.success('登录成功')
    }
    router.push('/dashboard')
  } catch (e: any) {
    const msg = e.message || (isRegisterMode.value ? '注册失败' : '登录失败，请检查用户名和密码')
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 装饰背景 -->
    <div class="bg-decoration">
      <div class="bg-circle c1"></div>
      <div class="bg-circle c2"></div>
      <div class="bg-circle c3"></div>
    </div>

    <div class="login-container">
      <!-- 品牌区 -->
      <div class="brand-section">
        <div class="brand-logo">A</div>
        <h1 class="brand-title">Agent<span class="accent">OS</span></h1>
        <p class="brand-sub">智能体操作系统</p>
        <div class="brand-features">
          <div class="feature-chip">🤖 ReAct Agent</div>
          <div class="feature-chip">🔧 MCP 工具生态</div>
          <div class="feature-chip">📚 RAG 知识库</div>
        </div>
      </div>

      <!-- 表单区 -->
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <h2>{{ formTitle }}</h2>
            <p>{{ formSubtitle }}</p>
          </div>
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            @keyup.enter="handleSubmit"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="'👤'"
              />
            </el-form-item>
            <el-form-item v-if="isRegisterMode" label="显示名称" prop="displayName">
              <el-input
                v-model="form.displayName"
                placeholder="选填，聊天时显示的名称"
                size="large"
                :prefix-icon="'✏️'"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                show-password
                :placeholder="isRegisterMode ? '请设置密码（至少6位）' : '请输入密码'"
                size="large"
                :prefix-icon="'🔒'"
              />
            </el-form-item>
            <el-form-item v-if="isRegisterMode" label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                show-password
                placeholder="请再次输入密码"
                size="large"
                :prefix-icon="'🔒'"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="handleSubmit"
                class="login-btn"
                size="large"
              >
                {{ submitText }}
              </el-button>
            </el-form-item>
          </el-form>
          <div class="form-footer">
            <button class="toggle-btn" @click="toggleMode">{{ toggleText }}</button>
            <span class="version">v2.0</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  position: relative;
  overflow: hidden;
}

/* 装饰背景 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.bg-circle {
  position: absolute;
  border-radius: 50%;
}
.c1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.04), transparent 70%);
  top: -200px;
  right: -200px;
}
.c2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.04), transparent 70%);
  bottom: -100px;
  left: -100px;
}
.c3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.03), transparent 70%);
  bottom: 40%;
  right: 20%;
}

.login-container {
  display: flex;
  width: 840px;
  max-width: 95vw;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* ===== 左侧品牌 ===== */
.brand-section {
  flex: 1;
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f8faff, #f5f3ff);
}
.brand-logo {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--accent), #7c3aed);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 24px;
}
.brand-title {
  font-size: 36px;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 6px;
  letter-spacing: -0.5px;
}
.accent { color: var(--accent); }
.brand-sub {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0 0 32px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.feature-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  font-size: 13px;
  color: var(--text-secondary);
  gap: 8px;
  box-shadow: var(--shadow-sm);
}

/* ===== 右侧表单 ===== */
.form-section {
  width: 400px;
  padding: 48px 40px;
  display: flex;
  align-items: center;
}
.form-card {
  width: 100%;
}
.form-header {
  margin-bottom: 32px;
}
.form-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px;
}
.form-header p {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-secondary);
  padding-bottom: 6px;
}
:deep(.el-input__prefix) {
  font-size: 16px;
  display: flex;
  align-items: center;
  margin-right: 4px;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 15px;
  margin-top: 8px;
}

.form-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
}
.toggle-btn {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  transition: opacity 0.2s;
}
.toggle-btn:hover {
  opacity: 0.75;
}
.version {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* ===== 响应式 ===== */
@media (max-width: 720px) {
  .login-container {
    flex-direction: column;
    width: 90vw;
    border-radius: var(--radius-lg);
  }
  .brand-section {
    padding: 32px 28px;
  }
  .brand-title {
    font-size: 28px;
  }
  .form-section {
    width: 100%;
    padding: 32px 28px;
  }
}
</style>
