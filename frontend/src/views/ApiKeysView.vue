<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUserApiKeysApi, createApiKeyApi, deleteApiKeyApi } from '@/api/api-keys'
import type { UserApiKey } from '@/api/api-keys'

const apiKeys = ref<UserApiKey[]>([])
const loading = ref(false)

const showCreateDialog = ref(false)
const newKey = ref({ provider: 'openai', apiKey: '', baseUrl: '' })
const creating = ref(false)

const providerOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Google (Gemini)', value: 'google' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Ollama', value: 'ollama' },
  { label: 'ModelScope', value: 'modelscope' },
  { label: '智谱', value: 'zhipu' },
]

async function fetchKeys() {
  loading.value = true
  try {
    const res = await getUserApiKeysApi()
    apiKeys.value = res.data.data
  } catch (e: any) {
    ElMessage.error(e.message || '获取 API Key 列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newKey.value.apiKey) {
    ElMessage.warning('请输入 API Key')
    return
  }
  creating.value = true
  try {
    await createApiKeyApi({
      provider: newKey.value.provider,
      apiKey: newKey.value.apiKey,
      baseUrl: newKey.value.baseUrl || undefined,
    })
    ElMessage.success('API Key 添加成功')
    showCreateDialog.value = false
    newKey.value = { provider: 'openai', apiKey: '', baseUrl: '' }
    fetchKeys()
  } catch (e: any) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(row: UserApiKey) {
  try {
    await ElMessageBox.confirm('确定要删除该 API Key 吗？', '确认删除', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteApiKeyApi(row.id)
    ElMessage.success('删除成功')
    fetchKeys()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

function maskApiKey(key: string): string {
  if (key.length > 8) {
    return key.slice(0, 4) + '****' + key.slice(-4)
  }
  return '****'
}

onMounted(fetchKeys)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>API Key 管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">+ 添加 Key</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="apiKeys" v-loading="loading" stripe empty-text="暂无 API Key">
        <el-table-column prop="provider" label="供应商" width="160" />
        <el-table-column label="API Key" min-width="280">
          <template #default="{ row }">
            {{ maskApiKey(row.apiKey) }}
          </template>
        </el-table-column>
        <el-table-column prop="baseUrl" label="Base URL" min-width="200">
          <template #default="{ row }">
            {{ row.baseUrl || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="isActive" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
              {{ row.isActive ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="添加 API Key" width="480px">
      <el-form :model="newKey" label-width="100px">
        <el-form-item label="供应商">
          <el-select v-model="newKey.provider" style="width: 100%">
            <el-option
              v-for="opt in providerOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input v-model="newKey.apiKey" placeholder="输入 API Key" show-password />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="newKey.baseUrl" placeholder="可选，自定义 API 地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          {{ creating ? '添加中...' : '添加' }}
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
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1d2129;
}
</style>
