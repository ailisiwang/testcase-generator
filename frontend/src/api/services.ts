import api from './index'

// 认证相关 API
export const authApi = {
  // 登录
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login', data),
  
  // 注册
  register: (data: { 
    username: string; 
    email: string; 
    password: string;
    employee_id?: string;
  }) =>
    api.post('/auth/register', data),
  
  // 刷新 Token
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  
  // 获取当前用户
  getCurrentUser: () =>
    api.get('/auth/me'),
}

// 用户管理 API
export const userApi = {
  // 获取用户列表
  getUsers: (params?: { page?: number; page_size?: number; keyword?: string }) =>
    api.get('/users', { params }),
  
  // 更新用户
  updateUser: (id: number, data: { username?: string; email?: string; employee_id?: string }) =>
    api.put(`/users/${id}`, data),
}

// 测试系统 API
export const systemApi = {
  // 获取系统列表
  getSystems: (params?: { page?: number; page_size?: number; keyword?: string }) =>
    api.get('/systems', { params }),
  
  // 获取系统详情
  getSystem: (id: number) =>
    api.get(`/systems/${id}`),
  
  // 创建系统
  createSystem: (data: { name: string; description?: string }) =>
    api.post('/systems', data),
  
  // 更新系统
  updateSystem: (id: number, data: { name?: string; description?: string }) =>
    api.put(`/systems/${id}`, data),
  
  // 删除系统
  deleteSystem: (id: number) =>
    api.delete(`/systems/${id}`),
  
  // 获取系统字段配置
  getSystemFields: (id: number) =>
    api.get(`/systems/${id}/fields`),
  
  // 更新系统字段配置
  updateSystemFields: (id: number, data: any[]) =>
    api.put(`/systems/${id}/fields`, data),
}

// 模块 API
export const moduleApi = {
  // 获取模块列表
  getModules: (systemId: number) =>
    api.get(`/systems/${systemId}/modules`),
  
  // 创建模块
  createModule: (systemId: number, data: { name: string; parent_id?: number; description?: string }) =>
    api.post(`/systems/${systemId}/modules`, data),
  
  // 更新模块
  updateModule: (id: number, data: { name?: string; parent_id?: number; description?: string }) =>
    api.put(`/modules/${id}`, data),
  
  // 删除模块
  deleteModule: (id: number) =>
    api.delete(`/modules/${id}`),
}

// 用例 API
export const caseApi = {
  // 获取用例列表
  getCases: (params?: { 
    system_id?: number; 
    module_id?: number;
    status?: string;
    page?: number; 
    page_size?: number;
    keyword?: string;
  }) =>
    api.get('/cases', { params }),
  
  // 获取用例详情
  getCase: (id: number) =>
    api.get(`/cases/${id}`),
  
  // 创建用例
  createCase: (data: { 
    system_id: number; 
    module_id?: number; 
    case_data: any;
  }) =>
    api.post('/cases', data),
  
  // 更新用例
  updateCase: (id: number, data: { 
    module_id?: number; 
    case_data?: any;
    status?: string;
  }) =>
    api.put(`/cases/${id}`, data),
  
  // 删除用例
  deleteCase: (id: number) =>
    api.delete(`/cases/${id}`),
  
  // 获取版本历史
  getCaseVersions: (id: number) =>
    api.get(`/cases/${id}/versions`),
  
  // 版本对比
  compareVersions: (id: number, v1: number, v2: number) =>
    api.get(`/cases/${id}/compare`, { params: { v1, v2 } }),
  
  // 导出 Excel
  exportCases: (params: { system_id?: number; module_id?: number; status?: string }) =>
    api.get('/cases/export', { params, responseType: 'blob' }),
}

// 用例生成 API
export const generateApi = {
  // 文本生成
  generateFromText: (data: { 
    system_id: number; 
    module_id?: number;
    requirement: string;
    model_config_id?: number;
  }) =>
    api.post('/cases/generate', data),
  
  // 文件生成
  generateFromFile: (formData: FormData) =>
    api.post('/cases/generate/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  // 流式输出
  getStream: (taskId: string) =>
    new EventSource(`/api/cases/generate/stream/${taskId}`),
}

// 模型配置 API
export const modelApi = {
  // 获取模型配置列表
  getModels: (params?: { page?: number; page_size?: number }) =>
    api.get('/models', { params }),
  
  // 获取模型详情
  getModel: (id: number) =>
    api.get(`/models/${id}`),
  
  // 创建模型配置
  createModel: (data: {
    provider: string;
    model_name: string;
    api_key?: string;
    api_base_url?: string;
    temperature?: number;
    max_tokens?: number;
  }) =>
    api.post('/models', data),
  
  // 更新模型配置
  updateModel: (id: number, data: {
    provider?: string;
    model_name?: string;
    api_key?: string;
    api_base_url?: string;
    temperature?: number;
    max_tokens?: number;
    is_active?: boolean;
  }) =>
    api.put(`/models/${id}`, data),
  
  // 删除模型配置
  deleteModel: (id: number) =>
    api.delete(`/models/${id}`),
  
  // 测试模型连接
  testModel: (id: number) =>
    api.post(`/models/${id}/test`),
}

// 日志 API
export const logApi = {
  // 获取操作日志
  getLogs: (params?: { 
    page?: number; 
    page_size?: number;
    action?: string;
    resource_type?: string;
  }) =>
    api.get('/logs', { params }),
}

export default api
