<script setup lang="ts">
import { reactive, ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAgentApi, createAgentApi, updateAgentApi } from '@/api/agents'
import { getToolsApi, getAgentToolsApi, bindToolsApi } from '@/api/tools'
import type { FormInstance } from 'element-plus'
import type { AgentFormData } from '@/types/agent'
import type { Tool } from '@/types/tool'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const formRef = ref<FormInstance>()
const loading = ref(false)
const pageLoading = ref(false)

const form = reactive<AgentFormData>({
  name: '',
  description: '',
  systemPrompt: '',
  modelProvider: 'openai',
  modelName: 'gpt-4o',
  temperature: 0.7,
  maxTokens: 2048,
})

const modelOptions = [
  { label: 'GPT-4o', value: 'gpt-4o' },
  { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
  { label: 'Gemini Pro', value: 'gemini-pro' },
  { label: 'DeepSeek', value: 'deepseek-chat' },
]

const rules = {
  name: [{ required: true, message: '请输入 Agent 名称', trigger: 'blur' }],
  systemPrompt: [{ required: true, message: '请输入系统提示词', trigger: 'blur' }],
}

// ==================== 工具绑定 ====================

const mcpTools = ref<Tool[]>([])
const boundToolIds = ref<number[]>([])
const loadingTools = ref(false)

async function loadToolsBinding() {
  if (!isEdit.value) return
  loadingTools.value = true
  try {
    const toolsRes = await getToolsApi({ page: 1, size: 999, source: 'mcp' })
    mcpTools.value = toolsRes.data.data.records
    const boundRes = await getAgentToolsApi(Number(route.params.id))
    boundToolIds.value = boundRes.data.data.map(t => t.id)
  } catch (e: any) {
    ElMessage.error(e.message || '加载工具列表失败')
  } finally {
    loadingTools.value = false
  }
}

watch(isEdit, (val) => {
  if (val) loadToolsBinding()
})

onMounted(async () => {
  if (isEdit.value) {
    pageLoading.value = true
    try {
      const id = Number(route.params.id)
      const res = await getAgentApi(id)
      const agent = res.data.data
      form.name = agent.name
      form.description = agent.description || ''
      form.systemPrompt = agent.systemPrompt
      form.modelProvider = agent.modelProvider || 'openai'
      form.modelName = agent.modelName
      form.temperature = agent.temperature ?? 0.7
      form.maxTokens = agent.maxTokens ?? 2048
      await loadToolsBinding()
    } catch (e: any) {
      ElMessage.error(e.message || '获取 Agent 信息失败')
      router.push('/agents')
    } finally {
      pageLoading.value = false
    }
  }
})

async function handleSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const id = Number(route.params.id)
    if (isEdit.value) {
      await updateAgentApi(id, form)
      if (mcpTools.value.length > 0) {
        await bindToolsApi(id, { toolIds: boundToolIds.value })
      }
      ElMessage.success('Agent 更新成功')
    } else {
      await createAgentApi(form)
      ElMessage.success('Agent 创建成功')
    }
    router.push('/agents')
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <h2>{{ isEdit ? '编辑 Agent' : '创建 Agent' }}</h2>
    </div>

    <el-card shadow="never" v-loading="pageLoading">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 700px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="给 Agent 起个名字" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="简要描述 Agent 的用途"
          />
        </el-form-item>

        <el-form-item label="系统提示词" prop="systemPrompt">
          <el-input
            v-model="form.systemPrompt"
            type="textarea"
            :rows="10"
            placeholder="设定 Agent 的角色和行为规则..."
          />
        </el-form-item>

        <el-form-item label="模型供应商" prop="modelProvider">
          <el-select v-model="form.modelProvider" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Google" value="google" />
            <el-option label="DeepSeek" value="deepseek" />
          </el-select>
        </el-form-item>

        <el-form-item label="模型" prop="modelName">
          <el-select v-model="form.modelName" style="width: 100%">
            <el-option
              v-for="opt in modelOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="温度" prop="temperature">
          <el-slider
            v-model="form.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            show-input
            style="width: 300px"
          />
          <span class="form-tip">值越高输出越有创造性，但可能降低准确性</span>
        </el-form-item>

        <el-form-item label="最大 Token" prop="maxTokens">
          <el-input-number
            v-model="form.maxTokens"
            :min="1"
            :max="32768"
            :step="256"
          />
        </el-form-item>

        <template v-if="isEdit">
          <el-divider />
          <el-form-item label="绑定工具" prop="tools">
            <div class="tool-binding-area">
              <div v-if="loadingTools" class="tool-loading">加载工具列表中...</div>
              <div v-else-if="mcpTools.length === 0" class="tool-empty">
                <span>暂无 MCP 工具可用，请先在</span>
                <router-link to="/tools" class="tool-link">工具中心</router-link>
                <span>注册 MCP 服务并同步工具。</span>
              </div>
              <el-select
                v-else
                v-model="boundToolIds"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="选择要绑定的 MCP 工具"
                style="width: 100%"
              >
                <el-option
                  v-for="tool in mcpTools"
                  :key="tool.id"
                  :label="tool.name"
                  :value="tool.id"
                >
                  <span>{{ tool.name }}</span>
                  <span class="tool-option-desc">{{ tool.description }}</span>
                </el-option>
              </el-select>
              <div class="form-tip">
                为 Agent 绑定 MCP 工具后，Agent 可在对话中自主调用这些工具。内置工具默认对所有 Agent 可用。
              </div>
            </div>
          </el-form-item>
        </template>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSave">
            {{ loading ? '保存中...' : '保存' }}
          </el-button>
          <el-button @click="router.push('/agents')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}
.form-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: 12px;
}
.tool-binding-area {
  width: 100%;
}
.tool-loading {
  color: var(--text-tertiary);
  font-size: 14px;
}
.tool-empty {
  color: var(--text-tertiary);
  font-size: 14px;
  padding: 8px 0;
}
.tool-empty .tool-link {
  color: var(--accent);
  margin: 0 4px;
}
.tool-option-desc {
  float: right;
  color: var(--text-tertiary);
  font-size: 12px;
  margin-left: 12px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
