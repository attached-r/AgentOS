<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMcpServersApi, createMcpServerApi, updateMcpServerApi, deleteMcpServerApi, syncMcpServerApi } from '@/api/mcp-servers'
import { getToolsApi } from '@/api/tools'
import type { McpServer, CreateMcpServerReq, UpdateMcpServerReq } from '@/types/mcp-server'
import type { Tool } from '@/types/tool'
import type { PageParams } from '@/types/api'

// ==================== MCP 服务器管理 ====================

const mcpServers = ref<McpServer[]>([])
const mcpLoading = ref(false)
const mcpTotal = ref(0)
const mcpPage = ref(1)

const mcpPageParams = reactive<PageParams>({ page: 1, size: 10 })

async function loadMcpServers() {
  mcpLoading.value = true
  try {
    const res = await getMcpServersApi({ page: mcpPageParams.page, size: mcpPageParams.size })
    mcpServers.value = res.data.data.records
    mcpTotal.value = res.data.data.total
  } catch (e: any) {
    ElMessage.error(e.message || '加载 MCP 服务列表失败')
  } finally {
    mcpLoading.value = false
  }
}

// ---- 注册弹窗 ----
const dialogVisible = ref(false)
const dialogTitle = ref('注册 MCP 服务')
const isEdit = ref(false)
const editId = ref<number | null>(null)
const formLoading = ref(false)

const form = reactive<CreateMcpServerReq>({
  name: '',
  description: '',
  endpoint: '',
  transport: 'sse',
})

function openCreateDialog() {
  isEdit.value = false
  editId.value = null
  dialogTitle.value = '注册 MCP 服务'
  form.name = ''
  form.description = ''
  form.endpoint = ''
  form.transport = 'sse'
  dialogVisible.value = true
}

function openEditDialog(row: McpServer) {
  isEdit.value = true
  editId.value = row.id
  dialogTitle.value = '编辑 MCP 服务'
  form.name = row.name
  form.description = row.description || ''
  form.endpoint = row.endpoint
  form.transport = row.transport
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name || !form.endpoint) {
    ElMessage.warning('请填写名称和端点地址')
    return
  }
  formLoading.value = true
  try {
    if (isEdit.value && editId.value) {
      const updateData: UpdateMcpServerReq = {
        name: form.name,
        description: form.description || undefined,
        endpoint: form.endpoint,
        transport: form.transport,
      }
      await updateMcpServerApi(editId.value, updateData)
      ElMessage.success('MCP 服务更新成功')
    } else {
      await createMcpServerApi(form)
      ElMessage.success('MCP 服务注册成功')
    }
    dialogVisible.value = false
    await loadMcpServers()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    formLoading.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该 MCP 服务吗？关联的工具也将被移除。', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteMcpServerApi(id)
    ElMessage.success('删除成功')
    await loadMcpServers()
    await loadTools()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

const syncingId = ref<number | null>(null)

async function handleSync(id: number) {
  syncingId.value = id
  try {
    await syncMcpServerApi(id)
    ElMessage.success('工具同步成功')
    await loadTools()
  } catch (e: any) {
    ElMessage.error(e.message || '同步失败')
  } finally {
    syncingId.value = null
  }
}

// ==================== 工具列表 ====================

const tools = ref<Tool[]>([])
const toolsLoading = ref(false)
const toolsTotal = ref(0)
const sourceFilter = ref('')

const toolPageParams = reactive<PageParams>({ page: 1, size: 10 })

async function loadTools() {
  toolsLoading.value = true
  try {
    const params: any = { page: toolPageParams.page, size: toolPageParams.size }
    if (sourceFilter.value) {
      params.source = sourceFilter.value
    }
    const res = await getToolsApi(params)
    tools.value = res.data.data.records
    toolsTotal.value = res.data.data.total
  } catch (e: any) {
    ElMessage.error(e.message || '加载工具列表失败')
  } finally {
    toolsLoading.value = false
  }
}

function formatSchema(schema: string | null): string {
  if (!schema) return '无'
  try {
    return JSON.stringify(JSON.parse(schema), null, 2)
  } catch {
    return schema
  }
}

const sourceOptions = [
  { label: '全部', value: '' },
  { label: '内置工具', value: 'builtin' },
  { label: 'MCP 工具', value: 'mcp' },
]

const transportOptions = [
  { label: 'SSE', value: 'sse' },
  { label: 'Stdio', value: 'stdio' },
]

onMounted(() => {
  loadMcpServers()
  loadTools()
})
</script>

<template>
  <div>
    <!-- ========== MCP 服务器管理 ========== -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header">
          <span>MCP 服务器管理</span>
          <el-button type="primary" size="small" @click="openCreateDialog">
            注册 MCP 服务
          </el-button>
        </div>
      </template>

      <el-table :data="mcpServers" v-loading="mcpLoading" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="endpoint" label="端点" min-width="200" show-overflow-tooltip />
        <el-table-column label="传输协议" width="100">
          <template #default="{ row }">
            <el-tag :type="row.transport === 'sse' ? 'primary' : 'warning'" size="small">
              {{ row.transport?.toUpperCase() || 'SSE' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="同步时间" width="170">
          <template #default="{ row }">
            {{ row.updatedAt ? new Date(row.updatedAt).toLocaleString() : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              size="small"
              type="primary"
              plain
              :loading="syncingId === row.id"
              @click="handleSync(row.id)"
            >
              {{ syncingId === row.id ? '同步中...' : '同步' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="mcpPageParams.page"
          v-model:page-size="mcpPageParams.size"
          :total="mcpTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadMcpServers"
        />
      </div>
    </el-card>

    <!-- ========== 工具列表 ========== -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header">
          <span>工具列表</span>
          <el-radio-group
            v-model="sourceFilter"
            size="small"
            @change="() => { toolPageParams.page = 1; loadTools() }"
          >
            <el-radio-button v-for="opt in sourceOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="tools" v-loading="toolsLoading" stripe style="width: 100%">
        <el-table-column prop="name" label="工具名称" min-width="140" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="来源" width="110">
          <template #default="{ row }">
            <el-tag :type="row.source === 'builtin' ? 'primary' : 'success'" size="small">
              {{ row.source === 'builtin' ? '内置' : 'MCP' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Schema 预览" min-width="200">
          <template #default="{ row }">
            <el-collapse>
              <el-collapse-item title="查看 Schema" name="schema">
                <pre class="schema-pre">{{ formatSchema(row.schema) }}</pre>
              </el-collapse-item>
            </el-collapse>
          </template>
        </el-table-column>
        <el-table-column label="同步时间" width="170">
          <template #default="{ row }">
            {{ row.syncedAt ? new Date(row.syncedAt).toLocaleString() : '—' }}
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="toolPageParams.page"
          v-model:page-size="toolPageParams.size"
          :total="toolsTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadTools"
        />
      </div>
    </el-card>

    <!-- ========== MCP 服务注册/编辑弹窗 ========== -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="MCP 服务名称" />
        </el-form-item>
        <el-form-item label="端点地址" required>
          <el-input v-model="form.endpoint" placeholder="http://localhost:8000/mcp" />
        </el-form-item>
        <el-form-item label="传输协议">
          <el-select v-model="form.transport" style="width: 100%">
            <el-option
              v-for="opt in transportOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="可选，描述该 MCP 服务的用途"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">
          {{ formLoading ? '保存中...' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.section-card {
  margin-bottom: 20px;
  border-radius: 12px !important;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-header span {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
}
.schema-pre {
  margin: 0;
  padding: 12px;
  background: #1d2129;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  max-height: 240px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #e6e6e6;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
</style>
