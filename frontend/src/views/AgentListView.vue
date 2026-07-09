<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAgentsApi, deleteAgentApi } from '@/api/agents'
import type { Agent } from '@/types/agent'

const router = useRouter()

const agents = ref<Agent[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)
const searchName = ref('')

async function fetchAgents() {
  loading.value = true
  try {
    const res = await getAgentsApi({
      page: page.value,
      size: size.value,
      name: searchName.value || undefined,
    })
    agents.value = res.data.data.records
    total.value = res.data.data.total
  } catch (e: any) {
    ElMessage.error(e.message || '获取 Agent 列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchAgents()
}

async function handleDelete(row: Agent) {
  try {
    await ElMessageBox.confirm(`确定要删除 Agent "${row.name}" 吗？`, '确认删除', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteAgentApi(row.id)
    ElMessage.success('删除成功')
    fetchAgents()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

onMounted(fetchAgents)
</script>

<template>
  <div class="agent-page">
    <!-- ===== 页面标题栏 + 搜索 ===== -->
    <div class="page-header">
      <div class="header-left">
        <h2>Agent 管理</h2>
        <span class="header-count" v-if="!loading">共 {{ total }} 个</span>
      </div>
      <button class="create-btn" @click="router.push('/agents/new')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        创建 Agent
      </button>
    </div>

    <!-- ===== 搜索栏 ===== -->
    <div class="search-bar">
      <div class="search-input-wrap">
        <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="searchName"
          class="search-input"
          placeholder="搜索 Agent 名称..."
          @keyup.enter="handleSearch"
        />
        <button v-if="searchName" class="search-clear" @click="searchName = ''; handleSearch()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <button class="search-submit" @click="handleSearch">搜索</button>
      <button class="search-reset" @click="searchName = ''; handleSearch()">重置</button>
    </div>

    <!-- ===== Loading 骨架屏 ===== -->
    <div v-if="loading" class="agent-grid">
      <div v-for="i in 6" :key="i" class="agent-card skeleton">
        <div class="skeleton-dot"></div>
        <div class="skeleton-line w-50"></div>
        <div class="skeleton-line w-30"></div>
        <div class="skeleton-line w-80"></div>
        <div class="skeleton-actions">
          <div class="skeleton-btn"></div>
          <div class="skeleton-btn"></div>
          <div class="skeleton-btn"></div>
        </div>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else-if="agents.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2"/>
          <path d="M8 21h8"/>
          <path d="M12 17v4"/>
        </svg>
      </div>
      <h3 class="empty-title">{{ searchName ? '未找到匹配的 Agent' : '暂无 Agent' }}</h3>
      <p class="empty-desc">{{ searchName ? '尝试修改搜索关键词' : '创建第一个 Agent 开始使用' }}</p>
      <button v-if="!searchName" class="empty-btn" @click="router.push('/agents/new')">创建 Agent</button>
      <button v-else class="empty-btn" @click="searchName = ''; handleSearch()">清除搜索</button>
    </div>

    <!-- ===== Agent 卡片网格 ===== -->
    <div v-else class="agent-grid">
      <div
        v-for="agent in agents"
        :key="agent.id"
        class="agent-card"
      >
        <!-- 卡片头部：状态灯 + 名称 -->
        <div class="agent-card-header">
          <span class="status-dot" :class="agent.status === 1 ? 'active' : 'inactive'"></span>
          <span class="agent-name">{{ agent.name }}</span>
        </div>

        <!-- 模型标签 -->
        <div class="agent-model">
          <span class="model-badge">{{ agent.modelName }}</span>
          <span v-if="agent.modelProvider" class="model-provider">{{ agent.modelProvider }}</span>
        </div>

        <!-- 描述 -->
        <p class="agent-desc">{{ agent.description || '暂无描述' }}</p>

        <!-- 底部操作栏 -->
        <div class="agent-card-actions">
          <button class="action-btn" @click="router.push(`/agents/${agent.id}/edit`)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            编辑
          </button>
          <button class="action-btn" @click="router.push(`/agents/${agent.id}/memories`)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            记忆
          </button>
          <button class="action-btn danger" @click="handleDelete(agent)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            删除
          </button>
        </div>
      </div>
    </div>

    <!-- ===== 分页 ===== -->
    <div v-if="total > size" class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="fetchAgents"
        @size-change="fetchAgents"
      />
    </div>
  </div>
</template>

<style scoped>
/* ============================================================
   Doubao 风格改造 — Phase B2
   AgentListView: el-table → Agent 卡片网格
   改动：移除 el-card + el-table + el-form（搜索），改为卡片网格
   保留：el-pagination 分页（全局覆盖样式）
   ============================================================ */

.agent-page {
  max-width: 1060px;
  margin: 0 auto;
}

/* ===== 页面标题栏 ===== */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
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
  gap: 6px;
  padding: 8px 18px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.create-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* ===== 搜索栏 ===== */
.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  align-items: center;
}
.search-input-wrap {
  flex: 1;
  position: relative;
  max-width: 360px;
}
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 8px 36px 8px 36px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: all var(--transition-fast);
}
.search-input:focus {
  border-color: var(--accent-light);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}
.search-input::placeholder {
  color: var(--text-tertiary);
}
.search-clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.search-clear:hover {
  background: var(--border-default);
  color: var(--text-secondary);
}
.search-submit {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.search-submit:hover {
  background: var(--accent-hover);
}
.search-reset {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.search-reset:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

/* ===== Agent 卡片网格 ===== */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

/* --- Agent 卡片 --- */
.agent-card {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid transparent;
}
.agent-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--accent-light);
}

/* 卡片头部：状态灯 + 名称 */
.agent-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.active {
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}
.status-dot.inactive {
  background: #d2d2d7;
}
.agent-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 模型标签 */
.agent-model {
  display: flex;
  align-items: center;
  gap: 8px;
}
.model-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 12px;
  font-weight: 500;
}
.model-provider {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 描述 */
.agent-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

/* 底部操作栏 */
.agent-card-actions {
  display: flex;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid var(--border-subtle);
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.action-btn:hover {
  background: var(--bg-secondary);
  color: var(--accent);
  border-color: var(--accent-light);
}
.action-btn.danger:hover {
  background: #fef2f2;
  color: var(--color-danger);
  border-color: #fecaca;
}

/* ===== 骨架屏 ===== */
.agent-card.skeleton {
  cursor: default;
  pointer-events: none;
  border-color: transparent;
}
.agent-card.skeleton:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
}
.skeleton-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #f8f8f8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #f8f8f8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.w-50 { width: 50%; }
.skeleton-line.w-30 { width: 30%; }
.skeleton-line.w-80 { width: 80%; }
.skeleton-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  margin-top: auto;
}
.skeleton-btn {
  height: 26px;
  width: 60px;
  border-radius: 6px;
  background: linear-gradient(90deg, #f0f0f0 25%, #f8f8f8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

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

/* ===== 分页 ===== */
.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
