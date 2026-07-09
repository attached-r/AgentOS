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

// 展开 schema 的 tool id
const expandedSchemaId = ref<number | null>(null)

function toggleSchema(id: number) {
  expandedSchemaId.value = expandedSchemaId.value === id ? null : id
}

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
  <div class="tools-page">
    <!-- ============================================================
         Section 1: MCP 服务器管理
         ============================================================ -->
    <section class="section-card">
      <div class="section-header">
        <div class="section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
            <line x1="6" y1="18" x2="6.01" y2="18"/>
          </svg>
          <span>MCP 服务器管理</span>
        </div>
        <button class="section-add-btn" @click="openCreateDialog">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          注册 MCP 服务
        </button>
      </div>

      <!-- Loading -->
      <div v-if="mcpLoading" class="mcp-grid">
        <div v-for="i in 3" :key="i" class="mcp-card skeleton">
          <div class="skeleton-line w-50"></div>
          <div class="skeleton-line w-80"></div>
          <div class="skeleton-line w-30"></div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="mcpServers.length === 0" class="section-empty">
        <p>暂无 MCP 服务器，点击上方按钮注册一个</p>
      </div>

      <!-- MCP 卡片列表 -->
      <div v-else class="mcp-grid">
        <div
          v-for="server in mcpServers"
          :key="server.id"
          class="mcp-card"
        >
          <div class="mcp-card-top">
            <div class="mcp-name">{{ server.name }}</div>
            <span class="mcp-status-tag" :class="server.status === 1 ? 'on' : 'off'">
              {{ server.status === 1 ? '已启用' : '已禁用' }}
            </span>
          </div>

          <div class="mcp-endpoint">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <code>{{ server.endpoint }}</code>
          </div>

          <div class="mcp-meta">
            <span class="mcp-transport-tag">
              {{ server.transport?.toUpperCase() || 'SSE' }}
            </span>
            <span v-if="server.updatedAt" class="mcp-time">
              同步 {{ new Date(server.updatedAt).toLocaleString() }}
            </span>
          </div>

          <div v-if="server.description" class="mcp-desc">{{ server.description }}</div>

          <div class="mcp-card-actions">
            <button class="mcp-action-btn" @click="openEditDialog(server)">编辑</button>
            <button
              class="mcp-action-btn primary"
              :disabled="syncingId === server.id"
              @click="handleSync(server.id)"
            >
              {{ syncingId === server.id ? '同步中...' : '同步' }}
            </button>
            <button class="mcp-action-btn danger" @click="handleDelete(server.id)">删除</button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="mcpTotal > mcpPageParams.size" class="pagination-wrap">
        <el-pagination
          v-model:current-page="mcpPageParams.page"
          v-model:page-size="mcpPageParams.size"
          :total="mcpTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadMcpServers"
          small
        />
      </div>
    </section>

    <!-- ============================================================
         Section 2: 工具列表
         ============================================================ -->
    <section class="section-card">
      <div class="section-header">
        <div class="section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
          </svg>
          <span>工具列表</span>
        </div>
        <div class="filter-chips">
          <button
            v-for="opt in [{ label: '全部', value: '' }, { label: '内置工具', value: 'builtin' }, { label: 'MCP 工具', value: 'mcp' }]"
            :key="opt.value"
            class="filter-chip"
            :class="{ active: sourceFilter === opt.value }"
            @click="sourceFilter = opt.value; toolPageParams.page = 1; loadTools()"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="toolsLoading" class="tool-grid">
        <div v-for="i in 4" :key="i" class="tool-card skeleton">
          <div class="skeleton-line w-40"></div>
          <div class="skeleton-line w-70"></div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="tools.length === 0" class="section-empty">
        <p>暂无工具数据{{ sourceFilter ? '（当前筛选条件下）' : '' }}</p>
      </div>

      <!-- 工具卡片列表 -->
      <div v-else class="tool-grid">
        <div
          v-for="tool in tools"
          :key="tool.id"
          class="tool-card"
        >
          <div class="tool-card-top">
            <div class="tool-name">{{ tool.name }}</div>
            <span class="tool-source-tag" :class="tool.source">
              {{ tool.source === 'builtin' ? '内置' : 'MCP' }}
            </span>
          </div>

          <p class="tool-desc">{{ tool.description || '暂无描述' }}</p>

          <div class="tool-schema-area">
            <button
              class="tool-schema-toggle"
              @click="toggleSchema(tool.id)"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
              Schema 预览
            </button>
            <pre v-if="expandedSchemaId === tool.id" class="tool-schema-body">{{ formatSchema(tool.schema) }}</pre>
          </div>

          <div v-if="tool.syncedAt" class="tool-meta">
            同步于 {{ new Date(tool.syncedAt).toLocaleString() }}
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="toolsTotal > toolPageParams.size" class="pagination-wrap">
        <el-pagination
          v-model:current-page="toolPageParams.page"
          v-model:page-size="toolPageParams.size"
          :total="toolsTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadTools"
          small
        />
      </div>
    </section>

    <!-- ============================================================
         MCP 服务注册/编辑弹窗（保留 Element Plus，全局样式已覆盖）
         ============================================================ -->
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
/* ============================================================
   Doubao 风格改造 — Phase C1
   ToolCenterView: el-table → MCP/工具卡片列表
   改动：MCP 服务器 el-table → 卡片网格，工具列表 el-table → 卡片网格
   移除：el-collapse schema 预览 → 点击展开
   保留：el-dialog 弹窗、el-pagination 分页（全局覆盖样式）
   ============================================================ */

.tools-page {
  max-width: 1060px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ===== 分区卡片 ===== */
.section-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 20px 24px 24px;
}

/* ===== 分区头部 ===== */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.section-add-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.section-add-btn:hover {
  background: var(--accent-hover);
}

/* ===== 筛选 Chip ===== */
.filter-chips {
  display: flex;
  gap: 6px;
}
.filter-chip {
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.filter-chip:hover {
  border-color: var(--accent-light);
  color: var(--accent);
}
.filter-chip.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

/* ===== MCP 卡片网格 ===== */
.mcp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}

/* --- MCP 卡片 --- */
.mcp-card {
  padding: 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mcp-card:hover {
  border-color: var(--accent-light);
  box-shadow: var(--shadow-sm);
}
.mcp-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.mcp-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mcp-status-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 999px;
  flex-shrink: 0;
}
.mcp-status-tag.on {
  background: #dcfce7;
  color: #16a34a;
}
.mcp-status-tag.off {
  background: #f3f4f6;
  color: #6b7280;
}

.mcp-endpoint {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-tertiary);
}
.mcp-endpoint code {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

.mcp-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}
.mcp-transport-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 2px 8px;
  border-radius: 4px;
}
.mcp-time {
  font-size: 11px;
  color: var(--text-tertiary);
}

.mcp-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.4;
}

.mcp-card-actions {
  display: flex;
  gap: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--border-subtle);
}
.mcp-action-btn {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.mcp-action-btn:hover {
  background: var(--bg-secondary);
  color: var(--accent);
  border-color: var(--accent-light);
}
.mcp-action-btn.primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.mcp-action-btn.primary:hover {
  background: var(--accent-hover);
}
.mcp-action-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.mcp-action-btn.danger:hover {
  background: #fef2f2;
  color: var(--color-danger);
  border-color: #fecaca;
}

/* ===== 工具卡片网格 ===== */
.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

/* --- 工具卡片 --- */
.tool-card {
  padding: 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tool-card:hover {
  border-color: var(--accent-light);
  box-shadow: var(--shadow-sm);
}
.tool-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.tool-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.tool-source-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 999px;
  flex-shrink: 0;
}
.tool-source-tag.builtin {
  background: var(--accent-soft);
  color: var(--accent);
}
.tool-source-tag.mcp {
  background: #ecfdf5;
  color: #059669;
}

.tool-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* Schema 预览 */
.tool-schema-area {
  margin-top: 4px;
}
.tool-schema-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 4px;
  border: none;
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.tool-schema-toggle:hover {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}
.tool-schema-toggle svg {
  transition: transform var(--transition-fast);
}
.tool-schema-toggle:hover svg {
  transform: rotate(90deg);
}
.tool-schema-body {
  margin: 8px 0 0;
  padding: 12px;
  background: #1e1e1e;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.5;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #d4d4d4;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

.tool-meta {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* ===== 骨架屏 ===== */
.mcp-card.skeleton,
.tool-card.skeleton {
  cursor: default;
  pointer-events: none;
  border-color: var(--border-subtle);
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
.skeleton-line.w-50 { width: 50%; }
.skeleton-line.w-80 { width: 80%; }
.skeleton-line.w-40 { width: 40%; }
.skeleton-line.w-70 { width: 70%; }
.skeleton-line.w-30 { width: 30%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ===== 空状态 ===== */
.section-empty {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 14px;
}

/* ===== 分页 ===== */
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
