import request from './request'
import type { ApiResponse, PageParams, PageResult } from '@/types/api'
import type { Agent, AgentFormData } from '@/types/agent'

export function getAgentsApi(params: PageParams & { name?: string }) {
  return request.get<ApiResponse<PageResult<Agent>>>('/agents', { params })
}

export function getAgentApi(id: number) {
  return request.get<ApiResponse<Agent>>(`/agents/${id}`)
}

export function createAgentApi(data: AgentFormData) {
  return request.post<ApiResponse<Agent>>('/agents', data)
}

export function updateAgentApi(id: number, data: AgentFormData) {
  return request.put<ApiResponse<Agent>>(`/agents/${id}`, data)
}

export function deleteAgentApi(id: number) {
  return request.delete<ApiResponse<null>>(`/agents/${id}`)
}

export function invokeAgentApi(id: number, prompt: string) {
  return request.post<ApiResponse<string>>(`/agents/${id}/invoke`, { prompt })
}
