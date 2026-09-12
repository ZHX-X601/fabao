/**
 * http.js —— axios 实例封装
 * 统一处理：
 * 1. 基础地址（开发环境走 Vite 代理 /api，生产环境需配置）
 * 2. 请求头自动携带 JWT token
 * 3. 响应统一解包 { code, message, data } 格式
 * 4. 错误统一处理
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const http = axios.create({
  baseURL: '/api/v1', // 后端接口统一前缀；开发环境经 Vite 代理转发到 localhost:8000
  timeout: 120000 // 请求超时 120 秒（AI 回复可能较慢）
})

// ========== 请求拦截器：自动注入 JWT token ==========
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fabao_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ========== 响应拦截器：统一解包后端响应格式 ==========
http.interceptors.response.use(
  (response) => {
    // 文件下载（blob 响应）直接返回，不做 JSON 解包
    if (response.config.responseType === 'blob') {
      return response.data
    }
    const res = response.data
    // 后端统一返回 { code, message, data }，code=200 为成功
    if (res.code === 200) {
      return res.data // 直接返回 data 字段，业务层不用再解构
    }
    // 业务错误（如用户名已存在、参数错误等）
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  (error) => {
    // HTTP 状态码错误
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        // 未登录或 token 过期：清除本地凭据并提示
        localStorage.removeItem('fabao_token')
        localStorage.removeItem('fabao_user')
        ElMessage.error('登录已过期，请重新登录')
      } else {
        ElMessage.error(data?.message || `请求错误 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else {
      ElMessage.error('网络异常，请检查后端服务是否启动')
    }
    return Promise.reject(error)
  }
)

export default http
