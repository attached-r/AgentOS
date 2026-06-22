import request from './request'
import type { ApiResponse, PageParams, PageResult } from '@/types/api'
import type { McpServer, CreateMcpServerReq, UpdateMcpServerReq } from '@/types/mcp-server'

export function createMcpServerApi(data: CreateMcpServerReq) {
  return request.post<ApiResponse<McpServer>>('/mcp-servers', data)
}

export function getMcpServersApi(params: PageParams) {
  return request.get<ApiResponse<PageResult<McpServer>>>('/mcp-servers', { params })
}

export function updateMcpServerApi(id: number, data: UpdateMcpServerReq) {
  return request.put<ApiResponse<McpServer>>(`/mcp-servers/${id}`, data)
}

export function deleteMcpServerApi(id: number) {
  return request.delete<ApiResponse<null>>(`/mcp-servers/${id}`)
}

export function syncMcpServerApi(id: number) {
  return request.post<ApiResponse<null>>(`/mcp-servers/${id}/sync`)
}
