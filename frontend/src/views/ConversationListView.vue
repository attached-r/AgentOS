<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getConversationsApi, createConversationApi, deleteConversationApi } from '@/api/conversations'
import { getAgentsApi } from '@/api/agents'
import type { Conversation } from '@/types/conversation'
import type { Agent } from '@/types/agent'

const router = useRouter()

const conversations = ref<Conversation[]>([])
const agents = ref<Agent[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(10)
const loading = ref(false)

const showCreateDialog = ref(false)
const newConversation = ref({ title: '', agentId: null as number | null })
const creating = ref(false)

async function fetchConversations() {
  loading.value = true
  try {
    const res = await getConversationsApi({ page: page.value, size: size.value })
    conversations.value = res.data.data.records
    total.value = res.data.data.total
  } catch (e: any) {
    ElMessage.error(e.message || '获取对话列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchAgents() {
  try {
    const res = await getAgentsApi({ page: 1, size: 100 })
    agents.value = res.data.data.records
  } catch {
    // 静默失败
  }
}

async function handleCreate() {
  if (!newConversation.value.agentId) {
    ElMessage.warning('请选择 Agent')
    return
  }
  creating.value = true
  try {
    const res = await createConversationApi({
      title: newConversation.value.title || undefined,
      agentId: newConversation.value.agentId,
    })
    ElMessage.success('对话创建成功')
    showCreateDialog.value = false
    router.push(`/conversations/${res.data.data.id}`)
  } catch (e: any) {
    ElMessage.error(e.message || '创建对话失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(row: Conversation) {
  try {
    await ElMessageBox.confirm('确定要删除该对话吗？', '确认删除', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteConversationApi(row.id)
    ElMessage.success('删除成功')
    fetchConversations()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

function openCreateDialog() {
  newConversation.value = { title: '', agentId: null }
  fetchAgents()
  showCreateDialog.value = true
}

function goToChat(id: number) {
  router.push(`/conversations/${id}`)
}

function getAgentName(agentId: number): string {
  const agent = agents.value.find(a => a.id === agentId)
  return agent?.name || `Agent #${agentId}`
}

// ============================================================
// Doubao 风格改造 — Phase B1
// 工具函数：格式化时间
// ============================================================

function formatTime(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

/**
 * 根据 agentId 生成固定的头像颜色
 */
const avatarColors = [
  'linear-gradient(135deg, #6366f1, #8b5cf6)',
  'linear-gradient(135deg, #3b82f6, #06b6d4)',
  'linear-gradient(135deg, #10b981, #34d399)',
  'linear-gradient(135deg, #f59e0b, #f97316)',
  'linear-gradient(135deg, #ef4444, #f43f5e)',
  'linear-gradient(135deg, #ec4899, #a855f7)',
]

function getAvatarColor(agentId: number): string {
  return avatarColors[agentId % avatarColors.length]
}

onMounted(() => {
  fetchConversations()
  fetchAgents()
})
</script>

<template>
  <div class="conv-page">
    <!-- ===== 页面标题栏 ===== -->
    <div class="page-header">
      <div class="header-left">
        <h2>对话列表</h2>
        <span class="header-count" v-if="!loading">共 {{ total }} 条</span>
      </div>
      <button class="create-btn" @click="openCreateDialog">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        新对话
      </button>
    </div>

    <!-- ===== Loading 骨架屏 ===== -->
    <div v-if="loading" class="conv-list">
      <div v-for="i in 4" :key="i" class="conv-card skeleton">
        <div class="conv-card-left">
          <div class="skeleton-avatar"></div>
        </div>
        <div class="conv-card-body">
          <div class="skeleton-line w-60"></div>
          <div class="skeleton-line w-40"></div>
          <div class="skeleton-line w-30"></div>
        </div>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else-if="conversations.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          <line x1="12" y1="9" x2="16" y2="9"/>
          <line x1="12" y1="13" x2="16" y2="13"/>
          <line x1="8" y1="9" x2="8.01" y2="9"/>
          <line x1="8" y1="13" x2="8.01" y2="13"/>
        </svg>
      </div>
      <h3 class="empty-title">暂无对话</h3>
      <p class="empty-desc">创建一个新对话，开始与 AI Agent 交流</p>
      <button class="empty-btn" @click="openCreateDialog">开始第一个对话</button>
    </div>

    <!-- ===== 对话卡片列表 ===== -->
    <div v-else class="conv-list">
      <!-- 对话卡片 -->
      <div
        v-for="conv in conversations"
        :key="conv.id"
        class="conv-card"
        @click="goToChat(conv.id)"
      >
        <!-- Agent 头像 -->
        <div class="conv-card-left">
          <div
            class="conv-avatar"
            :style="{ background: getAvatarColor(conv.agentId) }"
          >
            {{ getAgentName(conv.agentId).charAt(0).toUpperCase() }}
          </div>
        </div>

        <!-- 卡片内容 -->
        <div class="conv-card-body">
          <div class="conv-title">{{ conv.title || `对话 ${conv.id}` }}</div>
          <div class="conv-agent-name">{{ getAgentName(conv.agentId) }}</div>
          <div class="conv-meta">
            <span class="conv-time">{{ formatTime(conv.createdAt) }}</span>
            <span
              class="conv-status"
              :class="conv.status === 'active' ? 'status-active' : 'status-done'"
            >
              {{ conv.status === 'active' ? '进行中' : '已完成' }}
            </span>
          </div>
        </div>

        <!-- 删除按钮（hover 显示） -->
        <div class="conv-card-actions">
          <button
            class="delete-btn"
            title="删除对话"
            @click.stop="handleDelete(conv)"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
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
        layout="total, prev, pager, next"
        @current-change="fetchConversations"
      />
    </div>

    <!-- ===== 新建对话弹窗（保留 Element Plus，全局样式已覆盖） ===== -->
    <el-dialog v-model="showCreateDialog" title="新建对话" width="420px">
      <el-form :model="newConversation" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="newConversation.title" placeholder="可选，留空自动生成" />
        </el-form-item>
        <el-form-item label="Agent" required>
          <el-select v-model="newConversation.agentId" placeholder="请选择 Agent" style="width: 100%">
            <el-option
              v-for="agent in agents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          {{ creating ? '创建中...' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* ============================================================
   Doubao 风格改造 — Phase B1
   ConversationListView: el-table → 对话卡片列表
   改动：移除 el-card + el-table + el-table-column，改为卡片网格
   保留：el-dialog 创建弹窗、el-pagination 分页（全局覆盖样式）
   ============================================================ */

.conv-page {
  max-width: 880px;
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
.create-btn:active {
  transform: translateY(0);
}

/* ===== 对话卡片网格 ===== */
.conv-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

/* --- 对话卡片 --- */
.conv-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 18px 20px;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  border: 1px solid transparent;
}
.conv-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
  border-color: var(--accent-light);
}

/* Agent 头像 */
.conv-card-left {
  flex-shrink: 0;
}
.conv-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
}

/* 卡片主体 */
.conv-card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.conv-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-agent-name {
  font-size: 13px;
  color: var(--text-tertiary);
}
.conv-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 2px;
}
.conv-time {
  font-size: 12px;
  color: var(--text-tertiary);
}
.conv-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.5;
}
.status-active {
  background: #dcfce7;
  color: #16a34a;
}
.status-done {
  background: #f3f4f6;
  color: #6b7280;
}

/* 删除按钮（hover 显示） */
.conv-card-actions {
  position: absolute;
  top: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.conv-card:hover .conv-card-actions {
  opacity: 1;
}
.delete-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.delete-btn:hover {
  background: #fef2f2;
  color: var(--color-danger);
}

/* ===== 骨架屏 ===== */
.conv-card.skeleton {
  cursor: default;
  pointer-events: none;
  border-color: transparent;
}
.conv-card.skeleton:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
  border-color: transparent;
}
.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
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
  margin-bottom: 8px;
}
.skeleton-line:last-child {
  margin-bottom: 0;
}
.skeleton-line.w-60 { width: 60%; }
.skeleton-line.w-40 { width: 40%; }
.skeleton-line.w-30 { width: 30%; }

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

/* ===== 响应式：桌面端 2 列 ===== */
@media (min-width: 768px) {
  .conv-list {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
