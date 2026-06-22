import request from './request'
import type { ApiResponse, PageParams, PageResult } from '@/types/api'
import type { AgentMemory } from '@/types/memory'

export function getAgentMemoriesApi(agentId: number, params: PageParams) {
  return request.get<ApiResponse<PageResult<AgentMemory>>>(`/agents/${agentId}/memories`, { params })
}

export function deleteAgentMemoryApi(agentId: number, memId: number) {
  return request.delete<ApiResponse<null>>(`/agents/${agentId}/memories/${memId}`)
}
