<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getConversationApi, getMessagesApi, sendMessageApi } from '@/api/conversations'
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

// 加载历史消息
onMounted(async () => {
  try {
    const [convRes, msgRes] = await Promise.all([
      getConversationApi(conversationId),
      getMessagesApi(conversationId),
    ])
    conversationTitle.value = convRes.data.data.title || `对话 ${conversationId}`
    messages.value = msgRes.data.data
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
          <div class="message-avatar">
            <el-avatar :size="36" :icon="msg.role === 'user' ? undefined : undefined">
              {{ msg.role === 'user' ? 'U' : 'A' }}
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-bubble" :class="msg.role">
              <div class="bubble-text">{{ msg.content }}</div>
            </div>
          </div>
        </div>

        <!-- 发送中指示器 -->
        <div v-if="sending" class="message-row assistant-row">
          <div class="message-avatar">
            <el-avatar :size="36">A</el-avatar>
          </div>
          <div class="message-content">
            <div class="message-bubble assistant">
              <div class="typing-indicator">
                <span class="dot">.</span>
                <span class="dot">.</span>
                <span class="dot">.</span>
              </div>
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
  height: calc(100vh - 50px - 40px); /* 减去 header + main padding */
  background: #fff;
  border-radius: 4px;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  flex-shrink: 0;
}
.chat-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.center-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.message-row {
  display: flex;
  margin-bottom: 16px;
  gap: 12px;
}
.message-row.user-row {
  flex-direction: row-reverse;
}
.message-row.user-row .message-content {
  display: flex;
  justify-content: flex-end;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 10px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
  white-space: pre-wrap;
}
.message-bubble.user {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message-bubble.assistant {
  background: #fff;
  color: #303133;
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 4px;
}

.bubble-text {
  margin: 0;
}

/* 打字指示器动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 8px;
}
.dot {
  animation: blink 1.4s infinite both;
  font-size: 24px;
  line-height: 1;
  color: #909399;
}
.dot:nth-child(2) {
  animation-delay: 0.2s;
}
.dot:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}

.error-row {
  padding: 8px 0;
}

.input-area {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  background: #fff;
  flex-shrink: 0;
  align-items: flex-end;
}
.input-area .el-textarea {
  flex: 1;
}
.send-btn {
  height: 74px;
  width: 80px;
}
</style>
