// Agent 长期记忆实体（对应后端 AgentMemory）
export interface AgentMemory {
  id: number
  agentId: number
  userId: number
  memoryType: string    // "working" | "episodic" | "semantic"
  content: string
  importance: number
  metadata: string | null
  createdAt: string
}
