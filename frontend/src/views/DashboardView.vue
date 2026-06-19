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

    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ agentCount !== null ? agentCount : 'N/A' }}</div>
          <div class="stat-label">Agent 总数</div>
          <div class="stat-action">
            <el-button text type="primary" @click="router.push('/agents')">管理 Agent →</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ conversationCount !== null ? conversationCount : 'N/A' }}</div>
          <div class="stat-label">对话总数</div>
          <div class="stat-action">
            <el-button text type="primary" @click="router.push('/conversations')">查看对话 →</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ taskCount !== null ? taskCount : 'N/A' }}</div>
          <div class="stat-label">任务日志</div>
          <div class="stat-action">
            <el-button text type="primary" disabled>查看详情 →</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

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
}
.welcome-section h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #303133;
}
.welcome-desc {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
.stats-row {
  margin-bottom: 24px;
}
.stat-card {
  text-align: center;
  padding: 12px 0;
}
.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #409eff;
  line-height: 1.2;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin: 8px 0;
}
.stat-action {
  margin-top: 8px;
}
.recent-card {
  margin-top: 20px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
