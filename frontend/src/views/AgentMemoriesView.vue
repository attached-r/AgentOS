<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAgentApi } from '@/api/agents'
import { getAgentMemoriesApi, deleteAgentMemoryApi } from '@/api/memories'
import type { AgentMemory } from '@/types/memory'
import type { Agent } from '@/types/agent'
import type { PageParams } from '@/types/api'

const route = useRoute()
const router = useRouter()
const agentId = Number(route.params.id)

const agent = ref<Agent | null>(null)
const memories = ref<AgentMemory[]>([])
const loading = ref(false)
const total = ref(0)
const pageParams = reactive<PageParams>({ page: 1, size: 10 })

const memoryTypeMap: Record<string, { label: string; type: string }> = {
  working: { label: '工作记忆', type: 'primary' },
  episodic: { label: '情景记忆', type: 'success' },
  semantic: { label: '语义记忆', type: 'warning' },
}

async function loadAgent() {
  try {
    const res = await getAgentApi(agentId)
    agent.value = res.data.data
  } catch {
    // Agent 信息加载失败不阻塞
  }
}

async function loadMemories() {
  loading.value = true
  try {
    const res = await getAgentMemoriesApi(agentId, { page: pageParams.page, size: pageParams.size })
    memories.value = res.data.data.records
    total.value = res.data.data.total
  } catch (e: any) {
    ElMessage.error(e.message || '加载记忆失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(memId: number) {
  try {
    await ElMessageBox.confirm('确定要删除该条记忆吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteAgentMemoryApi(agentId, memId)
    ElMessage.success('删除成功')
    await loadMemories()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

function formatImportance(val: number): string {
  return (val * 100).toFixed(0) + '%'
}

onMounted(() => {
  loadAgent()
  loadMemories()
})
</script>

<template>
  <div class="memories-page">
    <!-- ===== 页面标题栏 ===== -->
    <div class="page-header">
      <button class="back-btn" @click="router.push('/agents')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        返回
      </button>
      <div class="header-title-group">
        <h2>{{ agent?.name || `Agent #${agentId}` }} — 长期记忆</h2>
        <span class="header-count" v-if="!loading">共 {{ total }} 条</span>
      </div>
    </div>

    <!-- ===== Loading 骨架屏 ===== -->
    <div v-if="loading" class="memories-list">
      <div v-for="i in 3" :key="i" class="memory-card skeleton">
        <div class="skeleton-line w-20"></div>
        <div class="skeleton-line w-90"></div>
        <div class="skeleton-line w-60"></div>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else-if="memories.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
      </div>
      <h3 class="empty-title">暂无长期记忆</h3>
      <p class="empty-desc">Agent 在对话中提取的重要信息将显示在这里</p>
    </div>

    <!-- ===== 记忆卡片列表 ===== -->
    <div v-else class="memories-list">
      <div
        v-for="mem in memories"
        :key="mem.id"
        class="memory-card"
      >
        <!-- 卡片头部：类型标签 + 时间 -->
        <div class="memory-card-header">
          <span
            class="memory-type-tag"
            :class="memoryTypeMap[mem.memoryType]?.type || 'info'"
          >
            {{ memoryTypeMap[mem.memoryType]?.label || mem.memoryType }}
          </span>
          <span class="memory-time">{{ new Date(mem.createdAt).toLocaleString() }}</span>
          <button
            class="memory-delete-btn"
            title="删除"
            @click="handleDelete(mem.id)"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>

        <!-- 记忆内容 -->
        <p class="memory-content">{{ mem.content }}</p>

        <!-- 底部：重要性进度条 -->
        <div class="memory-footer">
          <div class="memory-importance">
            <span class="importance-label">重要度</span>
            <div class="importance-bar-track">
              <div
                class="importance-bar-fill"
                :style="{ width: (mem.importance * 100) + '%' }"
                :class="mem.importance >= 0.7 ? 'high' : mem.importance >= 0.4 ? 'mid' : 'low'"
              ></div>
            </div>
            <span class="importance-value">{{ formatImportance(mem.importance) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 分页 ===== -->
    <div v-if="total > pageParams.size" class="pagination-wrap">
      <el-pagination
        v-model:current-page="pageParams.page"
        v-model:page-size="pageParams.size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadMemories"
      />
    </div>
  </div>
</template>

<style scoped>
/* ============================================================
   Doubao 风格改造 — Phase C3
   AgentMemoriesView: el-table → 记忆卡片列表
   改动：移除 el-table + el-empty，改为记忆卡片列表
   保留：el-pagination 分页（全局覆盖样式）
   ============================================================ */

.memories-page {
  max-width: 780px;
  margin: 0 auto;
}

/* ===== 页面标题栏 ===== */
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}
.back-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}
.header-title-group {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.header-title-group h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}
.header-count {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* ===== 记忆卡片列表 ===== */
.memories-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* --- 记忆卡片 --- */
.memory-card {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.memory-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--accent-light);
}

/* 卡片头部 */
.memory-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.memory-type-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 999px;
}
.memory-type-tag.primary {
  background: var(--accent-soft);
  color: var(--accent);
}
.memory-type-tag.success {
  background: #dcfce7;
  color: #16a34a;
}
.memory-type-tag.warning {
  background: #fef3c7;
  color: #d97706;
}
.memory-type-tag.info {
  background: #f3f4f6;
  color: #6b7280;
}
.memory-time {
  font-size: 12px;
  color: var(--text-tertiary);
  flex: 1;
}
.memory-delete-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
  opacity: 0;
}
.memory-card:hover .memory-delete-btn {
  opacity: 1;
}
.memory-delete-btn:hover {
  background: #fef2f2;
  color: var(--color-danger);
}

/* 记忆内容 */
.memory-content {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 底部 */
.memory-footer {
  padding-top: 8px;
  border-top: 1px solid var(--border-subtle);
}
.memory-importance {
  display: flex;
  align-items: center;
  gap: 10px;
}
.importance-label {
  font-size: 12px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}
.importance-bar-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: var(--bg-secondary);
  overflow: hidden;
}
.importance-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}
.importance-bar-fill.high {
  background: linear-gradient(90deg, #f59e0b, #ef4444);
}
.importance-bar-fill.mid {
  background: linear-gradient(90deg, #3b82f6, #6366f1);
}
.importance-bar-fill.low {
  background: linear-gradient(90deg, #9ca3af, #6b7280);
}
.importance-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
  min-width: 36px;
  text-align: right;
}

/* ===== 骨架屏 ===== */
.memory-card.skeleton {
  cursor: default;
  pointer-events: none;
  border-color: transparent;
}
.memory-card.skeleton:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
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
.skeleton-line.w-20 { width: 20%; }
.skeleton-line.w-90 { width: 90%; }
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
  margin: 0;
}

/* ===== 分页 ===== */
.pagination-wrap {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
