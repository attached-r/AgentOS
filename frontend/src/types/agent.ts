// Agent 实体（对应后端 Agent 实体）
export interface Agent {
  id: number
  name: string
  description: string | null
  systemPrompt: string
  modelProvider: string | null
  modelName: string
  temperature: number | null
  maxTokens: number | null
  avatarUrl: string | null
  ownerId: number
  status: number | null  // 0=stopped, 1=running
  createdAt: string
  updatedAt: string
}

// Agent 新建/编辑表单数据（对应 CreateAgentReq / UpdateAgentReq）
export interface AgentFormData {
  name: string
  description?: string
  systemPrompt: string
  modelProvider?: string
  modelName: string
  temperature?: number
  maxTokens?: number
}
