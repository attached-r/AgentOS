// 工具实体（对应后端 Tool）
export interface Tool {
  id: number
  mcpServerId: number | null
  name: string
  description: string | null
  schema: string | null       // JSON string（OpenAI function calling 格式）
  source: string              // "builtin" | "mcp"
  status: number
  versionHash: string | null
  createdAt: string
  syncedAt: string | null
}

// Agent 绑定工具请求
export interface BindToolsReq {
  toolIds: number[]
}
