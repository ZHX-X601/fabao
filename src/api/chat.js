/**
 * chat.js —— AI 法律咨询接口
 * 对接后端 /api/v1/chat/*
 * 对话历史与消息均持久化在后端数据库
 */

import http from '@/utils/http'

/** 获取当前用户的对话列表 */
export function getConversations() {
  return http.get('/chat/conversations')
}

/** 新建对话，返回对话信息（含 id） */
export function createConversation(title = '新的对话') {
  return http.post('/chat/conversations', { title })
}

/** 删除对话 */
export function deleteConversation(id) {
  return http.delete(`/chat/conversations/${id}`)
}

/** 获取某对话的消息列表 */
export function getMessages(conversationId) {
  return http.get(`/chat/conversations/${conversationId}/messages`)
}

/**
 * 发送消息，返回 AI 回复
 * @param {number} conversationId
 * @param {string} content
 */
export function sendMessage(conversationId, content) {
  return http.post(`/chat/conversations/${conversationId}/messages`, { content })
}
