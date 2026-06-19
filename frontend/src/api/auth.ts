import request from './request'
import type { ApiResponse } from '@/types/api'
import type { LoginRequest, LoginResp, RegisterRequest } from '@/types/auth'

export function loginApi(data: LoginRequest) {
  return request.post<ApiResponse<LoginResp>>('/auth/login', data)
}

export function registerApi(data: RegisterRequest) {
  return request.post<ApiResponse<LoginResp>>('/auth/register', data)
}

export function refreshApi() {
  return request.post<ApiResponse<LoginResp>>('/auth/refresh')
}

export function logoutApi() {
  return request.post<ApiResponse<null>>('/auth/logout')
}
