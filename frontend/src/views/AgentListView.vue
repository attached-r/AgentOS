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
  <div>
    <div class="page-header">
      <h2>Agent 管理</h2>
      <el-button type="primary" @click="router.push('/agents/new')">
        + 创建 Agent
      </el-button>
    </div>

    <el-card shadow="never">
      <el-form :inline="true" class="search-form">
        <el-form-item>
          <el-input
            v-model="searchName"
            placeholder="搜索 Agent 名称"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="searchName = ''; handleSearch()">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="agents" v-loading="loading" stripe empty-text="暂无 Agent 数据">
        <el-table-column label="名称" min-width="160">
          <template #default="{ row }">
            <div class="agent-name-cell">
              <span class="status-dot" :class="row.status === 1 ? 'active' : 'inactive'"></span>
              {{ row.name }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="modelName" label="模型" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small" effect="plain">
              {{ row.status === 1 ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="router.push(`/agents/${row.id}/edit`)">
              编辑
            </el-button>
            <el-button size="small" @click="router.push(`/agents/${row.id}/memories`)">
              记忆
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
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
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="fetchAgents"
          @size-change="fetchAgents"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.agent-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-dot {
  width: 7px;
  height: 7px;
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

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}
</style>
