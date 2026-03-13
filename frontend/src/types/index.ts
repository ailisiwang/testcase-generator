// 通用类型定义

// 用例数据结构
export interface CaseData {
  title: string
  precondition?: string
  steps?: string[]
  expected?: string
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]
  created_at?: string
  generated_at?: string
}

// 测试用例
export interface TestCase {
  id: number
  system_id: number
  module_id?: number
  case_data: CaseData
  version: number
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  review_status: 'pending' | 'approved' | 'rejected'
  created_at: string
  updated_at: string
}

// 测试系统
export interface System {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
}

// 模块
export interface Module {
  id: number
  name: string
  parent_id: number | null
  description?: string
  children?: Module[]
  system_id?: number
}

// 模型配置
export interface ModelConfig {
  id: number
  name: string
  provider: string
  model_name: string
  api_base_url?: string
  temperature: number
  max_tokens: number
  is_active: boolean
  is_default?: boolean
  created_at: string
  updated_at: string
}

// 用户
export interface User {
  id: number
  username: string
  email: string
  employee_id?: string
}

// API响应分页
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// API错误响应
export interface ApiError {
  detail: string
  code?: string
}

// 生成任务状态
export interface GenerationTask {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  content?: string
  error?: string
}

// 流式输出事件
export interface StreamEvent {
  content?: string
  done?: boolean
  full_content?: string
  error?: string
}
