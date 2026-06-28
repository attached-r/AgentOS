<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getKnowledgeDocsApi, createKnowledgeDocApi, deleteKnowledgeDocApi, indexKnowledgeDocApi } from '@/api/knowledge'
import { getAgentsApi } from '@/api/agents'
import type { KnowledgeDoc, CreateKnowledgeDocReq } from '@/types/knowledge'
import type { Agent } from '@/types/agent'
import type { PageParams } from '@/types/api'

// ==================== 文档列表 ====================

const docs = ref<KnowledgeDoc[]>([])
const loading = ref(false)
const total = ref(0)
const pageParams = reactive<PageParams>({ page: 1, size: 10 })
const agentFilter = ref<number | undefined>(undefined)

// Agent 列表（用于筛选和关联）
const agents = ref<Agent[]>([])

const embeddingStatusMap: Record<number, { label: string; type: string }> = {
  0: { label: '未索引', type: 'info' },
  1: { label: '索引中', type: 'warning' },
  2: { label: '已索引', type: 'success' },
}

async function loadDocs() {
  loading.value = true
  try {
    const params: any = { page: pageParams.page, size: pageParams.size }
    if (agentFilter.value !== undefined) {
      params.agentId = agentFilter.value
    }
    const res = await getKnowledgeDocsApi(params)
    docs.value = res.data.data.records
    total.value = res.data.data.total
  } catch (e: any) {
    ElMessage.error(e.message || '加载文档列表失败')
  } finally {
    loading.value = false
  }
}

async function loadAgents() {
  try {
    const res = await getAgentsApi({ page: 1, size: 999 })
    agents.value = res.data.data.records
  } catch {
    // Agent 列表加载失败不阻塞页面
  }
}

function getAgentName(agentId: number | null): string {
  if (agentId === null) return '全局'
  const agent = agents.value.find(a => a.id === agentId)
  return agent?.name || `Agent #${agentId}`
}

// ==================== 新增文档 ====================

const dialogVisible = ref(false)
const formLoading = ref(false)
const docForm = reactive<CreateKnowledgeDocReq>({
  title: '',
  content: '',
  source: 'manual',
  agentId: undefined,
})

function openCreateDialog() {
  docForm.title = ''
  docForm.content = ''
  docForm.agentId = undefined
  dialogVisible.value = true
}

async function handleCreate() {
  if (!docForm.content) {
    ElMessage.warning('请输入文档内容')
    return
  }
  formLoading.value = true
  try {
    await createKnowledgeDocApi(docForm)
    ElMessage.success('文档创建成功')
    dialogVisible.value = false
    await loadDocs()
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    formLoading.value = false
  }
}

// ==================== 删除文档 ====================

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该文档吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteKnowledgeDocApi(id)
    ElMessage.success('删除成功')
    await loadDocs()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

// ==================== 触发索引 ====================

const indexingId = ref<number | null>(null)

async function handleIndex(id: number) {
  indexingId.value = id
  try {
    await indexKnowledgeDocApi(id)
    ElMessage.success('索引触发成功')
    await loadDocs()
  } catch (e: any) {
    ElMessage.error(e.message || '索引触发失败')
  } finally {
    indexingId.value = null
  }
}

onMounted(() => {
  loadDocs()
  loadAgents()
})
</script>

<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>知识库文档</span>
          <div class="header-right">
            <el-select
              v-model="agentFilter"
              placeholder="按 Agent 筛选"
              clearable
              size="small"
              style="width: 200px; margin-right: 12px"
              @change="() => { pageParams.page = 1; loadDocs() }"
            >
              <el-option label="全局文档" :value="undefined" />
              <el-option
                v-for="agent in agents"
                :key="agent.id"
                :label="agent.name"
                :value="agent.id"
              />
            </el-select>
            <el-button type="primary" size="small" @click="openCreateDialog">
              新增文档
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="docs" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
        <el-table-column label="所属 Agent" width="150">
          <template #default="{ row }">
            {{ getAgentName(row.agentId) }}
          </template>
        </el-table-column>
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">
              {{ row.source === 'manual' ? '手动录入' : row.source === 'upload' ? '上传' : '网页' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="向量状态" width="110">
          <template #default="{ row }">
            <el-tag :type="embeddingStatusMap[row.embeddingStatus]?.type || 'info'" size="small" effect="plain">
              {{ embeddingStatusMap[row.embeddingStatus]?.label || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunkCount" label="分块数" width="80" align="center" />
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ new Date(row.createdAt).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              plain
              :disabled="row.embeddingStatus !== 0"
              :loading="indexingId === row.id"
              @click="handleIndex(row.id)"
            >
              {{ indexingId === row.id ? '索引中...' : '构建索引' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pageParams.page"
          v-model:page-size="pageParams.size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadDocs"
        />
      </div>
    </el-card>

    <!-- 新增文档弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新增文档"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="docForm.title" placeholder="文档标题（可选）" />
        </el-form-item>
        <el-form-item label="关联 Agent">
          <el-select v-model="docForm.agentId" placeholder="不选则为全局文档" clearable style="width: 100%">
            <el-option
              v-for="agent in agents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="docForm.content"
            type="textarea"
            :rows="8"
            placeholder="请输入文档内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleCreate">
          {{ formLoading ? '创建中...' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-right {
  display: flex;
  align-items: center;
}
</style>
