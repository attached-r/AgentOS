import request from './request'
import type { ApiResponse, PageParams, PageResult } from '@/types/api'
import type { Conversation, CreateConversationRequest, Message, SendMessageRequest } from '@/types/conversation'

export function getConversationsApi(params: PageParams) {
  return request.get<ApiResponse<PageResult<Conversation>>>('/conversations', { params })
}

export function getConversationApi(id: number) {
  return request.get<ApiResponse<Conversation>>(`/conversations/${id}`)
}

export function createConversationApi(data: CreateConversationRequest) {
  return request.post<ApiResponse<Conversation>>('/conversations', data)
}

export function updateConversationApi(id: number, data: { title?: string; status?: string }) {
  return request.put<ApiResponse<Conversation>>(`/conversations/${id}`, data)
}

export function deleteConversationApi(id: number) {
  return request.delete<ApiResponse<null>>(`/conversations/${id}`)
}

export function getMessagesApi(id: number) {
  return request.get<ApiResponse<Message[]>>(`/conversations/${id}/messages`)
}

export function sendMessageApi(id: number, data: SendMessageRequest) {
  return request.post<ApiResponse<Message>>(`/conversations/${id}/messages`, data)
}
