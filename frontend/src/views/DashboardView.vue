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
  <div>
    <div class="welcome-section">
      <h2>欢迎回来，{{ displayName }}！</h2>
      <p class="welcome-desc">这是您的 AgentOS 控制台，在这里您可以管理 Agent 和对话。</p>
    </div>

    <div class="stats-row">
      <div class="stat-card-wrapper">
        <div class="stat-card stat-card-blue">
          <div class="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ agentCount !== null ? agentCount : 'N/A' }}</div>
            <div class="stat-label">Agent 总数</div>
          </div>
          <div class="stat-action">
            <el-button text type="primary" @click="router.push('/agents')">管理 →</el-button>
          </div>
        </div>
      </div>
      <div class="stat-card-wrapper">
        <div class="stat-card stat-card-green">
          <div class="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ conversationCount !== null ? conversationCount : 'N/A' }}</div>
            <div class="stat-label">对话总数</div>
          </div>
          <div class="stat-action">
            <el-button text type="primary" @click="router.push('/conversations')">查看 →</el-button>
          </div>
        </div>
      </div>
      <div class="stat-card-wrapper">
        <div class="stat-card stat-card-orange">
          <div class="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ taskCount !== null ? taskCount : 'N/A' }}</div>
            <div class="stat-label">任务日志</div>
          </div>
          <div class="stat-action">
            <el-button text type="primary" disabled>详情 →</el-button>
          </div>
        </div>
      </div>
    </div>

    <el-card shadow="never" class="recent-card">
      <template #header>
        <div class="card-header">
          <span>最近对话</span>
          <el-button text type="primary" @click="router.push('/conversations')">查看全部</el-button>
        </div>
      </template>
      <el-table
        :data="recentConversations"
        v-loading="loading"
        stripe
        empty-text="暂无对话记录"
        @row-click="(row: Conversation) => goToConversation(row.id)"
        style="cursor: pointer"
      >
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            {{ row.title || `对话 ${row.id}` }}
          </template>
        </el-table-column>
        <el-table-column prop="agentId" label="Agent ID" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '进行中' : '已完成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.welcome-section {
  margin-bottom: 24px;
  background: #fff;
  border-radius: 12px;
  padding: 24px 28px;
  border: 1px solid var(--color-border);
}
.welcome-section h2 {
  margin: 0 0 6px;
  font-size: 22px;
  color: var(--color-text-primary);
  font-weight: 700;
}
.welcome-desc {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 14px;
}

/* === 统计卡片 — Widget 风格 === */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}
.stat-card-wrapper {
  min-width: 0;
}
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  overflow: hidden;
}
.stat-card:hover {
  border-color: transparent;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}
/* 卡片顶部彩色条 */
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}
.stat-card-blue::before { background: linear-gradient(90deg, #409eff, #79bbff); }
.stat-card-green::before { background: linear-gradient(90deg, #67c23a, #95d475); }
.stat-card-orange::before { background: linear-gradient(90deg, #e6a23c, #f4d19e); }

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-card-blue .stat-icon {
  background: #ecf5ff;
  color: #409eff;
}
.stat-card-green .stat-icon {
  background: #f0f9eb;
  color: #67c23a;
}
.stat-card-orange .stat-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-info {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.stat-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1px;
}
.stat-card-blue .stat-value { color: #409eff; }
.stat-card-green .stat-value { color: #67c23a; }
.stat-card-orange .stat-value { color: #e6a23c; }
.stat-label {
  font-size: 14px;
  color: var(--color-text-muted);
}

/* 最近对话卡片 */
.recent-card {
  margin-top: 0;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
:deep(.recent-card .el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}
:deep(.recent-card .el-card__header span) {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}
</style>
