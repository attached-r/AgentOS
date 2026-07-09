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
  <div class="knowledge-page">
    <!-- ===== 页面标题栏 ===== -->
    <div class="page-header">
      <div class="header-left">
        <h2>知识库</h2>
        <span class="header-count" v-if="!loading">共 {{ total }} 篇</span>
      </div>
      <div class="header-actions">
        <div class="agent-filter-wrap">
          <el-select
            v-model="agentFilter"
            placeholder="按 Agent 筛选"
            clearable
            size="small"
            style="width: 180px"
            @change="() => { pageParams.page = 1; loadDocs() }"
          >
            <el-option label="全部文档" :value="undefined" />
            <el-option label="全局文档" :value="null as any" />
            <el-option
              v-for="agent in agents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            />
          </el-select>
        </div>
        <button class="create-btn" @click="openCreateDialog">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          新增文档
        </button>
      </div>
    </div>

    <!-- ===== Loading 骨架屏 ===== -->
    <div v-if="loading" class="doc-list">
      <div v-for="i in 4" :key="i" class="doc-card skeleton">
        <div class="skeleton-line w-50"></div>
        <div class="skeleton-line w-30"></div>
        <div class="skeleton-line w-70"></div>
      </div>
    </div>

    <!-- ===== 空状态 ===== -->
    <div v-else-if="docs.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
      </div>
      <h3 class="empty-title">知识库为空</h3>
      <p class="empty-desc">添加文档到知识库，Agent 可在对话中检索相关内容</p>
      <button class="empty-btn" @click="openCreateDialog">添加第一篇文档</button>
    </div>

    <!-- ===== 文档卡片列表 ===== -->
    <div v-else class="doc-list">
      <div
        v-for="doc in docs"
        :key="doc.id"
        class="doc-card"
      >
        <!-- 卡片头部 -->
        <div class="doc-card-header">
          <div class="doc-title-area">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <span class="doc-title">{{ doc.title || '未命名文档' }}</span>
          </div>
          <span class="doc-source-tag">{{ doc.source === 'manual' ? '手动录入' : doc.source === 'upload' ? '上传' : '网页' }}</span>
        </div>

        <!-- 内容预览 -->
        <p class="doc-preview">{{ doc.content?.slice(0, 150) }}{{ doc.content?.length > 150 ? '...' : '' }}</p>

        <!-- 元信息 -->
        <div class="doc-meta">
          <span class="doc-agent">{{ getAgentName(doc.agentId) }}</span>
          <span class="doc-chunks" v-if="doc.chunkCount">共 {{ doc.chunkCount }} 块</span>
          <span class="doc-time">{{ new Date(doc.createdAt).toLocaleString() }}</span>
        </div>

        <!-- 状态 + 操作 -->
        <div class="doc-card-footer">
          <!-- 嵌入状态指示 -->
          <div class="doc-embed-status">
            <span
              class="embed-dot"
              :class="embeddingStatusMap[doc.embeddingStatus]?.type || 'info'"
            ></span>
            <span>{{ embeddingStatusMap[doc.embeddingStatus]?.label || '未知' }}</span>
          </div>

          <div class="doc-actions">
            <button
              class="doc-action-btn primary"
              :disabled="doc.embeddingStatus !== 0"
              :class="{ indexing: indexingId === doc.id }"
              @click="handleIndex(doc.id)"
            >
              {{ indexingId === doc.id ? '索引中...' : '构建索引' }}
            </button>
            <button class="doc-action-btn danger" @click="handleDelete(doc.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 分页 ===== -->
    <div v-if="total > pageParams.size" class="pagination-wrap">
      <el-pagination
        v-model:current-page="pageParams.page"
        v-model:page-size="pageParams.size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadDocs"
      />
    </div>

    <!-- ===== 新增文档弹窗（保留 Element Plus，全局样式已覆盖） ===== -->
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
/* ============================================================
   Doubao 风格改造 — Phase C2
   KnowledgeView: el-table → 文档卡片列表
   改动：文档列表 el-table → 卡片列表，筛选栏自定义
   保留：el-dialog 新增弹窗、el-select 筛选、el-pagination（全局覆盖样式）
   ============================================================ */

.knowledge-page {
  max-width: 880px;
  margin: 0 auto;
}

/* ===== 页面标题栏 ===== */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
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
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.create-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 16px;
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
.create-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

/* ===== 文档卡片列表 ===== */
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* --- 文档卡片 --- */
.doc-card {
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.doc-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--accent-light);
}

/* 卡片头部 */
.doc-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.doc-title-area {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  min-width: 0;
}
.doc-title-area svg {
  flex-shrink: 0;
  color: var(--accent);
}
.doc-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-source-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

/* 内容预览 */
.doc-preview {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 元信息 */
.doc-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.doc-agent {
  color: var(--accent);
  font-weight: 500;
}
.doc-chunks {
  color: var(--text-tertiary);
}

/* 底部：状态 + 操作 */
.doc-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
}
.doc-embed-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.embed-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.embed-dot.info {
  background: #9ca3af;
}
.embed-dot.warning {
  background: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
}
.embed-dot.success {
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.doc-actions {
  display: flex;
  gap: 6px;
}
.doc-action-btn {
  padding: 4px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.doc-action-btn:hover {
  background: var(--bg-secondary);
  color: var(--accent);
  border-color: var(--accent-light);
}
.doc-action-btn.primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.doc-action-btn.primary:hover {
  background: var(--accent-hover);
}
.doc-action-btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.doc-action-btn.primary.indexing {
  opacity: 0.7;
  cursor: wait;
}
.doc-action-btn.danger:hover {
  background: #fef2f2;
  color: var(--color-danger);
  border-color: #fecaca;
}

/* ===== 骨架屏 ===== */
.doc-card.skeleton {
  cursor: default;
  pointer-events: none;
  border-color: transparent;
}
.doc-card.skeleton:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
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
.skeleton-line.w-30 { width: 30%; }
.skeleton-line.w-70 { width: 70%; }

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
</style>
