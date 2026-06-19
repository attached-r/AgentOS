// 通用 API 响应类型（对应后端 R<T>）
export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

// 分页请求参数
export interface PageParams {
  page: number  // 从 1 开始
  size: number
}

// MyBatis-Plus 分页响应
export interface PageResult<T> {
  records: T[]
  total: number
  size: number
  current: number
  pages?: number
}
