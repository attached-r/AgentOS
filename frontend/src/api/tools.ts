import request from './request'
import type { ApiResponse, PageParams, PageResult } from '@/types/api'
import type { Tool, BindToolsReq } from '@/types/tool'

export function getToolsApi(params: PageParams & { source?: string }) {
  return request.get<ApiResponse<PageResult<Tool>>>('/tools', { params })
}

export function bindToolsApi(agentId: number, data: BindToolsReq) {
  return request.post<ApiResponse<null>>(`/agents/${agentId}/tools`, data)
}

export function getAgentToolsApi(agentId: number) {
  return request.get<ApiResponse<Tool[]>>(`/agents/${agentId}/tools`)
}

export function unbindToolApi(agentId: number, toolId: number) {
  return request.delete<ApiResponse<null>>(`/agents/${agentId}/tools/${toolId}`)
}
