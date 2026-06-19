import request from './request'
import type { ApiResponse } from '@/types/api'

export interface UserApiKey {
  id: number
  userId: number
  provider: string
  apiKey: string
  baseUrl: string | null
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface CreateApiKeyRequest {
  provider: string
  apiKey: string
  baseUrl?: string
}

export function getUserApiKeysApi() {
  return request.get<ApiResponse<UserApiKey[]>>('/user-api-keys')
}

export function getApiKeyApi(id: number) {
  return request.get<ApiResponse<UserApiKey>>(`/user-api-keys/${id}`)
}

export function createApiKeyApi(data: CreateApiKeyRequest) {
  return request.post<ApiResponse<UserApiKey>>('/user-api-keys', data)
}

export function updateApiKeyApi(id: number, data: Partial<CreateApiKeyRequest> & { isActive?: boolean }) {
  return request.put<ApiResponse<UserApiKey>>(`/user-api-keys/${id}`, data)
}

export function deleteApiKeyApi(id: number) {
  return request.delete<ApiResponse<null>>(`/user-api-keys/${id}`)
}
