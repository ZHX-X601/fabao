/**
 * useAuth.js —— 认证状态管理
 * 提供当前用户信息、登录/注册/登出方法，状态持久化到 localStorage
 */

import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getMe } from '@/api/auth'

// 当前登录用户（全局单例，跨组件共享）
const user = ref(JSON.parse(localStorage.getItem('fabao_user') || 'null'))
// 登录状态
const isLoggedIn = computed(() => !!user.value)

/**
 * 用户登录
 * @param {{username:string, password:string}} credentials
 */
async function login(credentials) {
  const res = await loginApi(credentials)
  // 保存 token 和用户信息
  localStorage.setItem('fabao_token', res.access_token)
  localStorage.setItem('fabao_user', JSON.stringify(res.user))
  user.value = res.user
  return res
}

/**
 * 用户注册
 * @param {{username:string, email:string, password:string}} data
 */
async function register(data) {
  return registerApi(data)
}

/** 退出登录：清除本地凭据 */
function logout() {
  localStorage.removeItem('fabao_token')
  localStorage.removeItem('fabao_user')
  user.value = null
}

/** 启动时拉取最新用户信息（token 仍有效则刷新用户数据） */
async function fetchMe() {
  try {
    const res = await getMe()
    user.value = res
    localStorage.setItem('fabao_user', JSON.stringify(res))
  } catch {
    // token 无效时清除本地状态
    logout()
  }
}

export function useAuth() {
  return { user, isLoggedIn, login, register, logout, fetchMe }
}
