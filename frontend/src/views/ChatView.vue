<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getConversationApi, getMessagesApi, sendMessageApi } from '@/api/conversations'
import { getAgentApi } from '@/api/agents'
import { getAgentToolsApi } from '@/api/tools'
import type { Message } from '@/types/conversation'

const route = useRoute()
const router = useRouter()

const conversationId = Number(route.params.id)

const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(true)
const sending = ref(false)
const errorMsg = ref('')
const conversationTitle = ref('')
const scrollRef = ref<HTMLDivElement>()

// 记录当前 Agent 是否绑定了工具（用于显示"正在调用工具..."）
const hasTools = ref(false)

// 加载历史消息
onMounted(async () => {
  try {
    const [convRes, msgRes] = await Promise.all([
      getConversationApi(conversationId),
      getMessagesApi(conversationId),
    ])
    conversationTitle.value = convRes.data.data.title || `对话 ${conversationId}`
    messages.value = msgRes.data.data

    // 检查 Agent 是否绑定了工具
    try {
      const agentId = convRes.data.data.agentId
      if (agentId) {
        const toolsRes = await getAgentToolsApi(agentId)
        hasTools.value = toolsRes.data.data.length > 0
      }
    } catch {
      // 工具查询失败不阻塞
    }
  } catch (e: any) {
    ElMessage.error(e.message || '加载对话失败')
    router.push('/conversations')
  } finally {
    loading.value = false
    scrollToBottom()
  }
})

// 监听消息变化自动滚动
watch(messages, () => {
  nextTick(scrollToBottom)
}, { deep: true })

function scrollToBottom() {
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  }
}

async function handleSend() {
  const content = inputText.value.trim()
  if (!content || sending.value) return

  // 1. 乐观追加用户消息
  const tempMsg: Message = {
    id: Date.now(),
    conversationId,
    role: 'user',
    content,
    metadata: null,
    createdAt: new Date().toISOString(),
  }
  messages.value.push(tempMsg)
  inputText.value = ''
  sending.value = true
  errorMsg.value = ''

  try {
    // 2. 调用 API
    const res = await sendMessageApi(conversationId, { content })
    messages.value.push(res.data.data)
  } catch (e: any) {
    errorMsg.value = e.message || '消息发送失败'
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

function handleRetry() {
  // 从最后一条用户消息重新发送
  const lastUserMsg = [...messages.value].reverse().find(m => m.role === 'user')
  if (lastUserMsg) {
    inputText.value = lastUserMsg.content
    // 移除最后一条用户消息
    messages.value = messages.value.filter(m => m.id !== lastUserMsg.id)
    errorMsg.value = ''
    nextTick(() => {
      handleSend()
    })
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// ==================== 工具调用展示逻辑 ====================

/**
 * 工具调用步骤：从 message 的 metadata 中解析。
 * V2 修复：原实现尝试从文本中解析 Thought/Action 标记，
 * 但 ReActAgent 实际使用 OpenAI function calling（结构化调用），
 * 步骤数据已由 Runtime 通过响应中的 steps 字段返回，
 * 后端将其存入消息的 metadata.steps 中。
 */
interface ToolCallStep {
  step: number
  action: string
  input: string
  output: string
}

function getToolStepsFromMeta(msg: Message): ToolCallStep[] | null {
  if (!msg.metadata) return null
  try {
    const meta = JSON.parse(msg.metadata)
    if (meta.steps && Array.isArray(meta.steps) && meta.steps.length > 0) {
      return meta.steps as ToolCallStep[]
    }
  } catch {
    // metadata 解析失败，不阻塞展示
  }
  return null
}
</script>

<template>
  <div class="chat-page">
    <!-- 标题栏 -->
    <div class="chat-header">
      <el-button text @click="router.push('/conversations')">
        ← 返回
      </el-button>
      <span class="chat-title">{{ conversationTitle || `对话 ${conversationId}` }}</span>
    </div>

    <!-- 消息列表 -->
    <div class="message-list" ref="scrollRef">
      <!-- 加载中 -->
      <div v-if="loading" class="center-state">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 空状态 -->
      <div v-else-if="messages.length === 0 && !sending" class="center-state">
        <el-empty description="开始一段新的对话" />
      </div>

      <!-- 消息气泡 -->
      <template v-else>
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-row"
          :class="msg.role === 'user' ? 'user-row' : 'assistant-row'"
        >
          <div class="message-avatar" :class="msg.role === 'user' ? 'user-avatar' : 'assistant-avatar'">
            {{ msg.role === 'user' ? 'U' : 'A' }}
          </div>
          <div class="message-content">
            <!-- 用户消息 -->
            <template v-if="msg.role === 'user'">
              <div class="message-bubble user">
                <div class="bubble-text">{{ msg.content }}</div>
              </div>
            </template>

            <!-- Assistant 消息：从 metadata 解析工具调用步骤 -->
            <template v-else>
              <template v-if="getToolStepsFromMeta(msg) as ToolCallStep[] | null">
                <div class="tool-call-card">
                  <div class="tool-call-header">
                    <span class="tool-call-title">🔧 工具调用过程</span>
                  </div>
                  <div
                    v-for="(step, stepIdx) in getToolStepsFromMeta(msg)"
                    :key="stepIdx"
                    class="tool-call-step"
                  >
                    <div class="step-header">
                      <el-tag size="small" type="warning" class="step-tag">
                        #{{ step.step }} 调用工具
                      </el-tag>
                      <code class="step-tool-name">{{ step.action }}</code>
                    </div>
                    <div class="step-detail">
                      <span class="step-label">参数：</span>
                      <pre class="step-code">{{ step.input }}</pre>
                    </div>
                    <div class="step-detail">
                      <span class="step-label">结果：</span>
                      <pre class="step-code">{{ step.output }}</pre>
                    </div>
                  </div>
                </div>
                <!-- 普通文本消息：最终回答 -->
                <div class="message-bubble assistant">
                  <div class="bubble-text">{{ msg.content }}</div>
                </div>
              </template>

              <!-- 普通文本消息：直接展示 -->
              <template v-else>
                <div class="message-bubble assistant">
                  <div class="bubble-text">{{ msg.content }}</div>
                </div>
              </template>
            </template>
          </div>
        </div>

        <!-- 发送中指示器 -->
        <div v-if="sending" class="message-row assistant-row">
          <div class="message-avatar assistant-avatar">A</div>
          <div class="message-content">
            <div class="message-bubble assistant">
              <div class="typing-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <div v-if="hasTools" class="thinking-hint">正在调用工具...</div>
            </div>
          </div>
        </div>

        <!-- 错误 + 重试 -->
        <div v-if="errorMsg && !sending" class="error-row">
          <el-alert
            :title="errorMsg"
            type="error"
            show-icon
            :closable="false"
          >
            <template #action>
              <el-button size="small" type="danger" @click="handleRetry">重试</el-button>
            </template>
          </el-alert>
        </div>
      </template>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        :disabled="sending"
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        @keydown="handleKeydown"
        resize="none"
      />
      <el-button
        type="primary"
        :loading="sending"
        :disabled="!inputText.trim() || sending"
        @click="handleSend"
        class="send-btn"
      >
        {{ sending ? '发送中...' : '发送' }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - 48px);
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

/* === 顶栏 === */
.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border);
  background: #fff;
  flex-shrink: 0;
}
.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* === 消息列表 === */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  background: #f7f8fa;
}

.center-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 消息行 */
.message-row {
  display: flex;
  margin-bottom: 16px;
  gap: 10px;
  animation: msgIn 0.2s ease;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.message-row.user-row {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 72%;
}

/* 头像 */
.message-avatar {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  margin-top: 4px;
}
.user-avatar {
  background: linear-gradient(135deg, #409eff, #3a8ee6);
}
.assistant-avatar {
  background: linear-gradient(135deg, #67c23a, #5cadb0);
}

/* 气泡 */
.message-bubble {
  padding: 10px 16px;
  border-radius: 16px;
  line-height: 1.65;
  font-size: 14px;
  word-break: break-word;
  white-space: pre-wrap;
  position: relative;
}
.message-bubble.user {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message-bubble.assistant {
  background: #fff;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}
.bubble-text {
  margin: 0;
}

/* === 打字指示器 === */
.typing-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #bfc4cc;
  animation: dotPulse 1.2s infinite both;
}
.dot:nth-child(2) { animation-delay: 0.16s; }
.dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes dotPulse {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.35; }
  30% { transform: translateY(-5px); opacity: 1; }
}
.thinking-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 6px 4px 2px;
  border-top: 1px dashed var(--color-border);
}

/* === 工具调用卡片 — 步骤详情 === */
.tool-call-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 8px;
  border: 1px solid var(--color-border);
}
.tool-call-header {
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--color-border);
}
.tool-call-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.tool-call-step {
  padding: 10px 0;
  position: relative;
  border-left: 2px solid #e6a23c;
  margin-left: 6px;
  padding-left: 16px;
}
.tool-call-step:last-child {
  border-left-color: #67c23a;
  padding-bottom: 0;
}
.tool-call-step::before {
  content: '';
  position: absolute;
  left: -5px;
  top: 14px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e6a23c;
  border: 2px solid #fff;
}
.tool-call-step:last-child::before {
  background: #67c23a;
}
.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.step-tool-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  background: #f0f2f5;
  padding: 2px 10px;
  border-radius: 4px;
}
.step-detail {
  margin-top: 4px;
}
.step-label {
  font-size: 12px;
  color: var(--color-text-muted);
  display: block;
  margin-bottom: 2px;
}
.step-code {
  font-size: 12px;
  color: var(--color-text-secondary);
  background: #f7f8fa;
  padding: 6px 10px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

/* === 输入区 === */
.input-area {
  display: flex;
  gap: 10px;
  padding: 14px 20px 16px;
  border-top: 1px solid var(--color-border);
  background: #fff;
  flex-shrink: 0;
  align-items: flex-end;
}
.input-area .el-textarea { flex: 1; }
:deep(.input-area .el-textarea__inner) {
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  border: 1px solid var(--color-border);
  transition: border-color 0.2s, box-shadow 0.2s;
}
:deep(.input-area .el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}
.send-btn {
  height: 74px;
  width: 84px;
  border-radius: 10px;
  font-weight: 500;
  letter-spacing: 1px;
}

/* 错误 */
.error-row {
  padding: 8px 0;
}
</style>
