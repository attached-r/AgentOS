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
  <div>
    <div class="page-header">
      <el-button text @click="router.push('/agents')">← 返回 Agent 列表</el-button>
      <h2>{{ agent?.name || `Agent #${agentId}` }} — 长期记忆</h2>
    </div>

    <el-card shadow="never">
      <el-table :data="memories" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="记忆类型" width="120">
          <template #default="{ row }">
            <el-tag :type="memoryTypeMap[row.memoryType]?.type || 'info'" size="small">
              {{ memoryTypeMap[row.memoryType]?.label || row.memoryType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip />
        <el-table-column label="重要度" width="120" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round(row.importance * 100)"
              :stroke-width="12"
              :format="formatImportance"
              :status="row.importance >= 0.7 ? 'success' : row.importance >= 0.4 ? 'warning' : 'exception'"
            />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ new Date(row.createdAt).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && memories.length === 0" class="empty-state">
        <el-empty description="暂无长期记忆" />
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pageParams.page"
          v-model:page-size="pageParams.size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadMemories"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 8px 0 0;
  font-size: 22px;
  font-weight: 700;
  color: #1d2129;
}
.empty-state {
  padding: 40px 0;
}
</style>
