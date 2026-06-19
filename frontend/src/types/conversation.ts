// 对话实体
export interface Conversation {
  id: number
  title: string
  userId: number
  agentId: number
  status: string  // "active" | "completed" | "archived"
  createdAt: string
  updatedAt: string
}

// 创建对话请求
export interface CreateConversationRequest {
  title?: string
  agentId: number
}

// 消息实体
export interface Message {
  id: number
  conversationId: number
  role: string   // "user" | "assistant"
  content: string
  metadata: string | null  // JSON string，含 token 用量
  createdAt: string
}

// 发送消息请求
export interface SendMessageRequest {
  content: string
}
