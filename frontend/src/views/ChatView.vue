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
const inputRef = ref<HTMLTextAreaElement>()

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

function onInput() {
  const el = inputRef.value as HTMLTextAreaElement | undefined
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// ==================== 工具调用展示逻辑 ====================

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
    <!-- ===== 标题栏 ===== -->
    <div class="chat-header">
      <button class="back-btn" @click="router.push('/conversations')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
      <div class="chat-header-info">
        <span class="chat-title">{{ conversationTitle || `对话 ${conversationId}` }}</span>
        <span class="chat-status" v-if="sending">输入中...</span>
      </div>
    </div>

    <!-- ===== 消息列表 ===== -->
    <div class="message-list" ref="scrollRef">
      <!-- 加载中 -->
      <div v-if="loading" class="center-state">
        <div class="loading-spinner">
          <div class="spinner-dot"></div>
          <div class="spinner-dot"></div>
          <div class="spinner-dot"></div>
        </div>
        <span class="loading-text">加载对话历史...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="messages.length === 0 && !sending" class="center-state">
        <div class="empty-chat">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h3 class="empty-title">开始对话</h3>
          <p class="empty-desc">发送一条消息，开启与 AI Agent 的对话</p>
        </div>
      </div>

      <!-- 消息气泡 -->
      <template v-else>
        <div
          v-for="(msg, idx) in messages"
          :key="msg.id"
          class="message-row"
          :class="msg.role === 'user' ? 'user-row' : 'assistant-row'"
        >
          <!-- AI 头像（左侧） -->
          <div v-if="msg.role !== 'user'" class="msg-avatar ai-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/>
              <path d="M20 16.5A6 6 0 0 0 14 11h-4a6 6 0 0 0-6 5.5V20h16v-3.5z"/>
            </svg>
          </div>

          <div class="msg-content">
            <!-- 用户消息 -->
            <template v-if="msg.role === 'user'">
              <div class="bubble user-bubble">
                <div class="bubble-text">{{ msg.content }}</div>
              </div>
            </template>

            <!-- Assistant 消息 -->
            <template v-else>
              <!-- 工具调用步骤 -->
              <template v-if="getToolStepsFromMeta(msg)">
                <div class="tool-steps">
                  <div class="tool-steps-header">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                    </svg>
                    <span>工具调用</span>
                  </div>
                  <div
                    v-for="(step, si) in getToolStepsFromMeta(msg)"
                    :key="si"
                    class="tool-step"
                  >
                    <div class="step-head">
                      <span class="step-badge">{{ si + 1 }}</span>
                      <code class="step-tool">{{ step.action }}</code>
                    </div>
                    <div class="step-body">
                      <div class="step-block">
                        <span class="step-label">参数</span>
                        <pre class="step-code">{{ step.input }}</pre>
                      </div>
                      <div class="step-block">
                        <span class="step-label">结果</span>
                        <pre class="step-code">{{ step.output }}</pre>
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- 最终回答气泡 -->
              <div class="bubble ai-bubble">
                <div class="bubble-text">{{ msg.content }}</div>
              </div>
            </template>
          </div>

          <!-- 用户头像（右侧） -->
          <div v-if="msg.role === 'user'" class="msg-avatar user-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
        </div>

        <!-- 发送中指示器 -->
        <div v-if="sending" class="message-row assistant-row">
          <div class="msg-avatar ai-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/>
              <path d="M20 16.5A6 6 0 0 0 14 11h-4a6 6 0 0 0-6 5.5V20h16v-3.5z"/>
            </svg>
          </div>
          <div class="msg-content">
            <div class="bubble ai-bubble">
              <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
              <div v-if="hasTools" class="thinking-text">正在调用工具...</div>
            </div>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="errorMsg && !sending" class="error-row">
          <div class="error-card">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span class="error-text">{{ errorMsg }}</span>
            <button class="retry-btn" @click="handleRetry">重试</button>
          </div>
        </div>
      </template>
    </div>

    <!-- ===== 输入区域 ===== -->
    <div class="input-area">
      <div class="input-wrapper">
        <textarea
          ref="inputRef"
          v-model="inputText"
          :disabled="sending"
          placeholder="输入消息..."
          rows="1"
          @keydown="handleKeydown"
          @input="onInput"
        ></textarea>
        <button
          class="send-btn"
          :class="{ active: inputText.trim() && !sending }"
          :disabled="!inputText.trim() || sending"
          @click="handleSend"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
      <div class="input-footer">
        <span class="input-hint">Enter 发送 · Shift+Enter 换行</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============================================================
   Chat Page — Doubao 风格
   ============================================================ */

.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - 28px);
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  position: relative;
}

/* ============================
   顶栏
   ============================ */
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-primary);
  flex-shrink: 0;
}
.back-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}
.back-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}
.chat-header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.chat-status {
  font-size: 12px;
  color: var(--text-tertiary);
  animation: pulseStatus 1.5s ease infinite;
}
@keyframes pulseStatus {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ============================
   消息列表
   ============================ */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px;
  background: var(--bg-secondary);
}

.center-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
}

/* --- 加载动画 --- */
.loading-spinner {
  display: flex;
  gap: 8px;
}
.spinner-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  animation: spinnerBounce 1.2s infinite both;
  opacity: 0.3;
}
.spinner-dot:nth-child(2) { animation-delay: 0.16s; }
.spinner-dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes spinnerBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
  30% { transform: translateY(-8px); opacity: 1; }
}
.loading-text {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* --- 空状态 --- */
.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
}
.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--accent-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
}
.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.empty-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

/* --- 消息容器 --- */
/* 每条消息占据整行宽度，flex 控制内部对齐 */
.message-row {
  display: flex;
  margin-bottom: 16px;
  gap: 10px;
  width: 100%;
  animation: msgSlideIn 0.25s ease both;
}
@keyframes msgSlideIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 用户消息 → 整体推到右侧，头像靠右边缘，气泡在头像左边 */
.user-row {
  justify-content: flex-end;
}
/* AI 消息 → 整体在左侧，头像靠左边缘，气泡在头像右边 */
.assistant-row {
  justify-content: flex-start;
}

/* --- 头像 --- */
.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 4px;
}
.user-avatar {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  order: 1;                   /* 在 flex 布局中排最后 = 最右侧 */
}
.ai-avatar {
  background: var(--bg-primary);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

/* --- 消息内容容器 --- */
.msg-content {
  max-width: 72%;
  min-width: 0;
}

/* --- 气泡 --- */
.bubble {
  padding: 12px 16px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
  white-space: pre-wrap;
  position: relative;
}
.bubble-text {
  margin: 0;
}
.bubble-text:empty::after {
  content: ' ';
  display: inline-block;
}

/* 用户气泡 */
.user-bubble {
  background: linear-gradient(135deg, var(--accent), #4f46e5);
  color: #fff;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

/* AI 气泡 */
.ai-bubble {
  background: var(--bg-primary);
  color: var(--text-primary);
  border-radius: 18px 18px 18px 4px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-subtle);
}

/* --- 打字指示器 --- */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 0;
}
.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-tertiary);
  animation: dotPulse 1.2s infinite both;
}
.typing-dot:nth-child(2) { animation-delay: 0.16s; }
.typing-dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes dotPulse {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
  30% { transform: translateY(-5px); opacity: 1; }
}
.thinking-text {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 8px 4px 2px;
  border-top: 1px dashed var(--border-subtle);
  margin-top: 4px;
}

/* --- 工具调用步骤 --- */
.tool-steps {
  background: var(--bg-primary);
  border-radius: 14px;
  padding: 12px 14px;
  margin-bottom: 8px;
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
}
.tool-steps-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px dashed var(--border-subtle);
}
.tool-step {
  position: relative;
  padding: 8px 0 8px 20px;
  border-left: 2px solid #f59e0b;
  margin-bottom: 8px;
}
.tool-step:last-child {
  border-left-color: var(--color-success);
  margin-bottom: 0;
}
.tool-step::before {
  content: '';
  position: absolute;
  left: -5px;
  top: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
  border: 2px solid var(--bg-primary);
}
.tool-step:last-child::before {
  background: var(--color-success);
}
.step-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.step-badge {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fef3c7;
  color: #d97706;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-tool {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-secondary);
  padding: 2px 10px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}
.step-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.step-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.step-label {
  font-size: 11px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.step-code {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 6px 10px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

/* --- 错误卡片 --- */
.error-row {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}
.error-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fef2f2;
  border-radius: var(--radius-sm);
  color: var(--color-danger);
  font-size: 13px;
}
.retry-btn {
  margin-left: 8px;
  padding: 4px 12px;
  border: 1px solid var(--color-danger);
  border-radius: 6px;
  background: transparent;
  color: var(--color-danger);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.retry-btn:hover {
  background: var(--color-danger);
  color: #fff;
}

/* ============================
   输入区域 — Doubao 风格
   ============================ */
.input-area {
  flex-shrink: 0;
  padding: 12px 24px 16px;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-subtle);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 8px 8px 8px 18px;
  border: 2px solid transparent;
  transition: all var(--transition-fast);
}
.input-wrapper:focus-within {
  border-color: var(--accent-light);
  background: var(--bg-primary);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.06);
}

.input-wrapper textarea {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  resize: none;
  font-family: inherit;
  max-height: 120px;
  padding: 4px 0;
}
.input-wrapper textarea::placeholder {
  color: var(--text-tertiary);
}
.input-wrapper textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}
.send-btn.active {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}
.send-btn.active:hover {
  background: var(--accent-hover);
  transform: scale(1.05);
}
.send-btn:disabled {
  cursor: not-allowed;
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 6px;
}
.input-hint {
  font-size: 11px;
  color: var(--text-tertiary);
  letter-spacing: 0.3px;
}

/* ============================
   响应式
   ============================ */
@media (max-width: 768px) {
  .messages-container {
    padding: 0 12px;
  }
  .msg-content {
    max-width: 85%;
  }
  .input-area {
    padding: 10px 12px 14px;
  }
  .chat-title {
    font-size: 14px;
  }
}
</style>
