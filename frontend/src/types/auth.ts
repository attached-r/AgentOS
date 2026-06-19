// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应（对应后端 LoginResp 平铺结构）
export interface LoginResp {
  tokenName: string
  tokenValue: string
  userId: number
  username: string
  displayName: string
  avatarUrl: string | null
}

// 前端展示用的用户信息
export interface UserInfo {
  userId: number
  username: string
  displayName: string
  avatarUrl: string | null
}

// 注册请求
export interface RegisterRequest {
  username: string
  password: string
  displayName?: string
}
