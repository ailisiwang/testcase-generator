import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import Cookies from 'js-cookie'
import { message } from 'antd'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const cookieOptions = {
  sameSite: 'strict' as const,
  secure: window.location.protocol === 'https:',
  path: '/',
}

// 扩展 InternalAxiosRequestConfig 类型，添加 _retry 标记
interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = Cookies.get('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 是否正在刷新 token
let isRefreshing = false
// 存储等待刷新完成的请求
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<unknown>) => {
    const originalRequest = error.config as ExtendedAxiosRequestConfig

    // 网络错误处理
    if (!error.response && error.message) {
      if (error.message.includes('Network Error')) {
        message.error('网络连接失败，请检查网络设置')
      } else if (error.message.includes('timeout')) {
        message.error('请求超时，请稍后重试')
      } else if (error.message.includes('abort')) {
        // 请求被取消，不显示错误
      } else {
        message.error(`网络错误: ${error.message}`)
      }
      return Promise.reject(error)
    }

    // 如果没有 config 或没有 response，直接拒绝
    if (!originalRequest || !error.response) {
      return Promise.reject(error)
    }

    const { status } = error.response

    // 401 处理 - 刷新 token
    if (status === 401) {
      // 如果已经重试过，直接跳转登录
      if (originalRequest._retry) {
        Cookies.remove('access_token', { path: '/' })
        Cookies.remove('refresh_token', { path: '/' })
        // 清空认证状态
        window.location.href = '/login'
        return Promise.reject(error)
      }

      const refreshToken = Cookies.get('refresh_token')

      if (!refreshToken) {
        // 没有刷新 token，直接跳转登录
        Cookies.remove('access_token', { path: '/' })
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 标记为正在重试
      originalRequest._retry = true

      // 如果正在刷新，将请求加入队列
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return api(originalRequest)
          })
          .catch(err => {
            return Promise.reject(err)
          })
      }

      isRefreshing = true

      try {
        // 尝试刷新 token
        const res = await axios.post(`${BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token } = res.data
        Cookies.set('access_token', access_token, { ...cookieOptions, expires: 1 })

        processQueue(null, access_token)

        // 重新发送原始请求
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }

        return api(originalRequest)
      } catch (refreshError) {
        // 刷新失败
        processQueue(refreshError as Error, null)
        Cookies.remove('access_token', { path: '/' })
        Cookies.remove('refresh_token', { path: '/' })
        message.error('登录已过期，请重新登录')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 403 权限不足
    if (status === 403) {
      message.error('没有权限访问此资源')
      return Promise.reject(error)
    }

    // 404 资源不存在
    if (status === 404) {
      message.error('请求的资源不存在')
      return Promise.reject(error)
    }

    // 500 服务器错误
    if (status >= 500 && status < 600) {
      message.error('服务器错误，请稍后重试')
      return Promise.reject(error)
    }

    // 其他错误
    return Promise.reject(error)
  }
)

export default api
