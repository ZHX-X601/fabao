/**
 * document.js —— 文书生成接口
 * 对接后端 /api/v1/documents/*
 */

import http from '@/utils/http'

/**
 * 生成法律文书
 * @param {{doc_type:string, form_data:object}} data
 * doc_type: 起诉状 / 答辩状 / 律师函 / 授权委托书
 */
export function generateDocument(data) {
  return http.post('/documents/generate', data)
}

/** 获取某条文书记录详情 */
export function getDocument(id) {
  return http.get(`/documents/${id}`)
}

/** 获取当前用户的文书历史列表 */
export function getDocumentList() {
  return http.get('/documents/list')
}

/**
 * 下载文书为 Word 文件（返回 Blob）
 * @param {{content:string, doc_type:string}} data
 */
export function downloadDocument(data) {
  return http.post('/documents/download', data, { responseType: 'blob' })
}
