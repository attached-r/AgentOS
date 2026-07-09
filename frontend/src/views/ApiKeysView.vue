<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserApiKeysApi, createApiKeyApi, deleteApiKeyApi } from '@/api/api-keys'
import type { UserApiKey } from '@/api/api-keys'

const apiKeys = ref<UserApiKey[]>([])
const loading = ref(false)

const showCreateDialog = ref(false)
const newKey = ref({ provider: 'openai', apiKey: '', baseUrl: '' })
const creating = ref(false)

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Google (Gemini)', value: 'google' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Ollama', value: 'ollama' },
  { label: 'ModelScope', value: 'modelscope' },
  { label: '智谱', value: 'zhipu' },
]

async function fetchKeys() {
  loading.value = true
  try {
    const res = await getUserApiKeysApi()
    apiKeys.value = res.data.data
  } catch (e: any) {
    ElMessage.error(e.message || '获取 API Key 列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newKey.value.apiKey) {
    ElMessage.warning('请输入 API Key')
    return
  }
  creating.value = true
  try {
    await createApiKeyApi({
      provider: newKey.value.provider,
      apiKey: newKey.value.apiKey,
      baseUrl: newKey.value.baseUrl || undefined,
    })
    ElMessage.success('API Key 添加成功')
    showCreateDialog.value = false
    newKey.value = { provider: 'openai', apiKey: '', baseUrl: '' }
    fetchKeys()
  } catch (e: any) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(row: UserApiKey) {
  try {
    await ElMessageBox.confirm('确定要删除该 API Key 吗？', '确认删除', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteApiKeyApi(row.id)
    ElMessage.success('删除成功')
    fetchKeys()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

function maskApiKey(key: string): string {
  if (key.length > 8) {
    return key.slice(0, 4) + '****' + key.slice(-4)
  }
  return '****'
}

// 供应商图标（取前两个字母作为彩色标识）
const providerColors: Record<string, string> = {
  openai: 'linear-gradient(135deg, #10a37f, #1a7f5a)',
  google: 'linear-gradient(135deg, #4285f4, #34a853)',
  deepseek: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
  ollama: 'linear-gradient(135deg, #000, #333)',
  modelscope: 'linear-gradient(135deg, #eb4c4c, #f97316)',
  zhipu: 'linear-gradient(135deg, #2563eb, #06b6d4)',
}

function getProviderColor(provider: string): string {
  return providerColors[provider] || 'linear-gradient(135deg, #6366f1, #8b5cf6)'
}

function getProviderLabel(provider: string): string {
  const opt = providerOptions.find(p => p.value === provider)
  return opt?.label || provider
}

onMounted(fetchKeys)
</script>

<template>
  <div class="apikeys-page">
    <!-- ===== 页面标题栏 ===== -->
    <div class="page-header">
      <div class="header-left">
        <h2>API Key 管理</h2>
        <span class="header-count" v-if="!loading">共 {{ apiKeys.length }} 个</span>
      </div>
      <button class="create-btn" @click="showCreateDialog = true">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        添加 Key
      </button>
    </div>

    <!-- ===== Loading 骨架屏 ===== -->
    <div v-if="loading" class="apikey-list">
      <div v-for="i in 3" :key="i" class="apikey-card skeleton">
        <div class="skeleton-line w-30"></div>
        <div class="skeleton-line w-60"></div>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else-if="apiKeys.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
        </svg>
      </div>
      <h3 class="empty-title">暂无 API Key</h3>
      <p class="empty-desc">添加 API Key 以启用 LLM 调用</p>
      <button class="empty-btn" @click="showCreateDialog = true">添加第一个 Key</button>
    </div>

    <!-- ===== API Key 列表 ===== -->
    <div v-else class="apikey-list">
      <div
        v-for="key in apiKeys"
        :key="key.id"
        class="apikey-card"
      >
        <!-- 供应商彩色标识 -->
        <div class="apikey-provider-icon" :style="{ background: getProviderColor(key.provider) }">
          {{ key.provider.charAt(0).toUpperCase() }}
        </div>

        <!-- 详情 -->
        <div class="apikey-body">
          <div class="apikey-top">
            <span class="apikey-provider">{{ getProviderLabel(key.provider) }}</span>
            <span class="apikey-status" :class="key.isActive ? 'active' : 'inactive'">
              {{ key.isActive ? '启用' : '禁用' }}
            </span>
          </div>
          <div class="apikey-masked">{{ maskApiKey(key.apiKey) }}</div>
          <div class="apikey-meta">
            <span v-if="key.baseUrl" class="apikey-base-url">{{ key.baseUrl }}</span>
            <span class="apikey-time">{{ new Date(key.createdAt).toLocaleString() }}</span>
          </div>
        </div>

        <!-- 操作 -->
        <div class="apikey-actions">
          <button class="apikey-action-btn danger" @click="handleDelete(key)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- ===== 添加弹窗（保留 Element Plus，全局样式已覆盖） ===== -->
    <el-dialog v-model="showCreateDialog" title="添加 API Key" width="480px">
      <el-form :model="newKey" label-width="100px">
        <el-form-item label="供应商">
          <el-select v-model="newKey.provider" style="width: 100%">
            <el-option
              v-for="opt in providerOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input v-model="newKey.apiKey" placeholder="输入 API Key" show-password />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="newKey.baseUrl" placeholder="可选，自定义 API 地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          {{ creating ? '添加中...' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* ============================================================
   Doubao 风格改造 — Phase C4
   ApiKeysView: el-table → API Key 卡片列表
   改动：移除 el-card + el-table，改为列表项布局
   保留：el-dialog 弹窗（全局覆盖样式）
   ============================================================ */

.apikeys-page {
  max-width: 780px;
  margin: 0 auto;
}

/* ===== 页面标题栏 ===== */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.header-left h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}
.header-count {
  font-size: 13px;
  color: var(--text-tertiary);
}
.create-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 16px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.create-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

/* ===== API Key 列表 ===== */
.apikey-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* --- Key 卡片 --- */
.apikey-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  border: 1px solid transparent;
}
.apikey-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--accent-light);
}

/* 供应商图标 */
.apikey-provider-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}

/* 主体 */
.apikey-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.apikey-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.apikey-provider {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.apikey-status {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 8px;
  border-radius: 999px;
}
.apikey-status.active {
  background: #dcfce7;
  color: #16a34a;
}
.apikey-status.inactive {
  background: #f3f4f6;
  color: #6b7280;
}
.apikey-masked {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.apikey-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.apikey-base-url {
  color: var(--accent);
}

/* 操作 */
.apikey-actions {
  flex-shrink: 0;
}
.apikey-action-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.apikey-action-btn:hover {
  border-color: transparent;
}
.apikey-action-btn.danger:hover {
  background: #fef2f2;
  color: var(--color-danger);
}

/* ===== 骨架屏 ===== */
.apikey-card.skeleton {
  cursor: default;
  pointer-events: none;
  border-color: transparent;
}
.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #f8f8f8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  margin-bottom: 8px;
}
.skeleton-line:last-child { margin-bottom: 0; }
.skeleton-line.w-30 { width: 30%; }
.skeleton-line.w-60 { width: 60%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ===== 空状态 ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}
.empty-icon {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--accent-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  margin-bottom: 16px;
}
.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}
.empty-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0 0 24px;
}
.empty-btn {
  padding: 10px 24px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.empty-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}
</style>
