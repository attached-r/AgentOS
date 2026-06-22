import request from './request'
import type { ApiResponse, PageParams, PageResult } from '@/types/api'
import type { KnowledgeDoc, CreateKnowledgeDocReq } from '@/types/knowledge'

export function createKnowledgeDocApi(data: CreateKnowledgeDocReq) {
  return request.post<ApiResponse<KnowledgeDoc>>('/knowledge/docs', data)
}

export function getKnowledgeDocsApi(params: PageParams & { agentId?: number }) {
  return request.get<ApiResponse<PageResult<KnowledgeDoc>>>('/knowledge/docs', { params })
}

export function deleteKnowledgeDocApi(id: number) {
  return request.delete<ApiResponse<null>>(`/knowledge/docs/${id}`)
}

export function indexKnowledgeDocApi(id: number) {
  return request.post<ApiResponse<null>>(`/knowledge/docs/${id}/index`)
}
