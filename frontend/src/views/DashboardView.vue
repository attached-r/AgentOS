<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getAgentsApi } from '@/api/agents'
import { getConversationsApi } from '@/api/conversations'
import { getTaskLogsApi } from '@/api/task-logs'
import type { Conversation } from '@/types/conversation'

const router = useRouter()
const authStore = useAuthStore()

const agentCount = ref<number | null>(null)
const conversationCount = ref<number | null>(null)
const taskCount = ref<number | null>(null)
const recentConversations = ref<Conversation[]>([])
const loading = ref(true)

const displayName = authStore.user?.displayName || authStore.user?.username || 'User'

onMounted(async () => {
  try {
    const [agentRes, convRes, taskRes] = await Promise.allSettled([
      getAgentsApi({ page: 1, size: 1 }),
      getConversationsApi({ page: 1, size: 5 }),
      getTaskLogsApi({ page: 1, size: 1 }),
    ])

    if (agentRes.status === 'fulfilled') {
      agentCount.value = agentRes.value.data.data.total
    }
    if (convRes.status === 'fulfilled') {
      const pageData = convRes.value.data.data
      conversationCount.value = pageData.total
      recentConversations.value = pageData.records
    }
    if (taskRes.status === 'fulfilled') {
      taskCount.value = taskRes.value.data.data.total
    }
  } finally {
    loading.value = false
  }
})

function goToConversation(id: number) {
  router.push(`/conversations/${id}`)
}
</script>

<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-card">
      <div class="welcome-text">
        <h2>👋 欢迎回来，{{ displayName }}</h2>
        <p>这是您的 AgentOS 控制台，在这里可以管理 Agent 和对话。</p>
      </div>
      <div class="welcome-actions">
        <button class="action-btn primary" @click="router.push('/conversations')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          开始对话
        </button>
        <button class="action-btn" @click="router.push('/agents/new')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          创建 Agent
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon-box agents">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ agentCount !== null ? agentCount : '—' }}</div>
          <div class="stat-label">Agent 总数</div>
        </div>
        <a class="stat-link" @click="router.push('/agents')">管理 →</a>
      </div>

      <div class="stat-card">
        <div class="stat-icon-box chats">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ conversationCount !== null ? conversationCount : '—' }}</div>
          <div class="stat-label">对话总数</div>
        </div>
        <a class="stat-link" @click="router.push('/conversations')">查看 →</a>
      </div>

      <div class="stat-card">
        <div class="stat-icon-box tasks">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ taskCount !== null ? taskCount : '—' }}</div>
          <div class="stat-label">任务日志</div>
        </div>
        <a class="stat-link disabled">详情 →</a>
      </div>
    </div>

    <!-- 最近对话 -->
    <div class="section-card">
      <div class="section-header">
        <h3>最近对话</h3>
        <button class="section-more" @click="router.push('/conversations')">查看全部 →</button>
      </div>
      <div class="section-body">
        <div v-if="loading" class="loading-placeholder">
          <div class="placeholder-row" v-for="i in 3" :key="i"></div>
        </div>
        <table v-else-if="recentConversations.length > 0" class="simple-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>Agent ID</th>
              <th>状态</th>
              <th>创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in recentConversations"
              :key="row.id"
              @click="goToConversation(row.id)"
            >
              <td class="cell-title">{{ row.title || `对话 ${row.id}` }}</td>
              <td>{{ row.agentId }}</td>
              <td>
                <span class="status-tag" :class="row.status === 'active' ? 'success' : 'info'">
                  {{ row.status === 'active' ? '进行中' : '已完成' }}
                </span>
              </td>
              <td class="cell-date">{{ row.createdAt }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-section">
          <p>暂无对话记录</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 960px;
  margin: 0 auto;
}

/* ============================
   欢迎卡片
   ============================ */
.welcome-card {
  background: linear-gradient(135deg, #eef2ff, #f5f3ff);
  border-radius: var(--radius-lg);
  padding: 28px 32px;
  margin-bottom: 24px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}
.welcome-text h2 {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}
.welcome-text p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}
.welcome-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.action-btn:hover {
  border-color: var(--accent-light);
  color: var(--accent);
  background: var(--accent-soft);
}
.action-btn.primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.action-btn.primary:hover {
  background: var(--accent-hover);
}

/* ============================
   统计卡片
   ============================ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-icon-box.agents {
  background: #eef2ff;
  color: #4f46e5;
}
.stat-icon-box.chats {
  background: #ecfdf5;
  color: #059669;
}
.stat-icon-box.tasks {
  background: #fef3c7;
  color: #d97706;
}

.stat-body {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.stat-value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1px;
  color: var(--text-primary);
}
.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
  font-weight: 450;
}

.stat-link {
  font-size: 13px;
  color: var(--accent);
  cursor: pointer;
  font-weight: 500;
  text-decoration: none;
  transition: color var(--transition-fast);
}
.stat-link:hover {
  color: var(--accent-hover);
}
.stat-link.disabled {
  color: var(--text-tertiary);
  cursor: default;
  pointer-events: none;
}

/* ============================
   最近对话卡片
   ============================ */
.section-card {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
}
.section-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.section-more {
  background: none;
  border: none;
  color: var(--accent);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
}
.section-more:hover {
  color: var(--accent-hover);
}

.section-body {
  padding: 0;
}

/* 简约表格 */
.simple-table {
  width: 100%;
  border-collapse: collapse;
}
.simple-table th {
  text-align: left;
  padding: 10px 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-subtle);
}
.simple-table td {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 14px;
  color: var(--text-secondary);
}
.simple-table tbody tr {
  cursor: pointer;
  transition: background var(--transition-fast);
}
.simple-table tbody tr:hover {
  background: var(--accent-soft);
}
.simple-table tbody tr:last-child td {
  border-bottom: none;
}
.cell-title {
  font-weight: 500;
  color: var(--text-primary);
}
.cell-date {
  font-size: 13px;
  color: var(--text-tertiary);
}

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}
.status-tag.success {
  background: #dcfce7;
  color: #16a34a;
}
.status-tag.info {
  background: #f3f4f6;
  color: #6b7280;
}

/* Loading placeholder */
.loading-placeholder {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.placeholder-row {
  height: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #f8f8f8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.empty-section {
  padding: 40px;
  text-align: center;
  color: var(--text-tertiary);
}
</style>
