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

onMounted(() => {
  fetchConversations()
  fetchAgents()
})
</script>

<template>
  <div>
    <div class="page-header">
      <h2>对话列表</h2>
      <el-button type="primary" @click="openCreateDialog">+ 新对话</el-button>
    </div>

    <el-card shadow="never">
      <el-table
        :data="conversations"
        v-loading="loading"
        stripe
        empty-text="暂无对话"
        @row-click="(row: Conversation) => goToChat(row.id)"
        style="cursor: pointer"
      >
        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            {{ row.title || `对话 ${row.id}` }}
          </template>
        </el-table-column>
        <el-table-column label="Agent" width="160">
          <template #default="{ row }">
            {{ getAgentName(row.agentId) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '进行中' : '已完成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right" @click.stop>
          <template #default="{ row }">
            <el-button size="small" type="danger" @click.stop="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchConversations"
        />
      </div>
    </el-card>

    <!-- 新建对话对话框 -->
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
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
