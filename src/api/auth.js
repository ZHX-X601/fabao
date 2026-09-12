/**
 * auth.js —— 认证相关接口
 * 对接后端 /api/v1/auth/*
 */

import http from '@/utils/http'

/**
 * 用户注册
 * @param {{username:string, email:string, password:string}} data
 */
export function register(data) {
  return http.post('/auth/register', data)
}

/**
 * 用户登录，返回 token 和用户信息
 * @param {{username:string, password:string}} data
 */
export function login(data) {
  return http.post('/auth/login', data)
}

/**
 * 获取当前登录用户信息（需 token）
 */
export function getMe() {
  return http.get('/auth/me')
}
