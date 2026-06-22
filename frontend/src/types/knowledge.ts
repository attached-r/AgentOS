// 知识库文档实体（对应后端 KnowledgeDoc）
export interface KnowledgeDoc {
  id: number
  agentId: number | null
  title: string | null
  content: string
  source: string              // "manual" | "upload" | "web"
  chunkCount: number | null
  embeddingStatus: number     // 0=未索引 1=索引中 2=已索引
  createdAt: string
  updatedAt: string
}

// 新建知识库文档请求
export interface CreateKnowledgeDocReq {
  agentId?: number
  title?: string
  content: string
  source?: string
}
