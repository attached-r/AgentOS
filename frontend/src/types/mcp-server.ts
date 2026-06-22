// MCP 服务实体（对应后端 McpServer）
export interface McpServer {
  id: number
  name: string
  description: string | null
  endpoint: string
  transport: string  // "sse" | "stdio"
  status: number     // 1=启用 0=禁用
  createdAt: string
  updatedAt: string
}

// 注册 MCP 服务请求
export interface CreateMcpServerReq {
  name: string
  description?: string
  endpoint: string
  transport?: string
}

// 更新 MCP 服务请求
export interface UpdateMcpServerReq {
  name?: string
  description?: string
  endpoint?: string
  transport?: string
  status?: number
}
