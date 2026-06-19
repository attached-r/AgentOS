import request from './request'
import type { ApiResponse, PageParams, PageResult } from '@/types/api'

export interface TaskLog {
  id: number
  agentId: number
  level: string
  message: string
  createdAt: string
}

export function getTaskLogsApi(params: PageParams & { agentId?: number }) {
  return request.get<ApiResponse<PageResult<TaskLog>>>('/task-logs', { params })
}
