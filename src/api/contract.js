/**
 * contract.js —— 合同审查接口
 * 对接后端 /api/v1/contracts/*
 */

import http from '@/utils/http'

/**
 * 上传合同文件（.docx / .pdf），提取文本
 * @param {FormData} formData - 包含 file 字段
 */
export function uploadContract(formData) {
  return http.post('/contracts/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/** 对已上传的合同执行审查，返回风险结果 */
export function reviewContract(id) {
  return http.post(`/contracts/review/${id}`)
}

/** 获取当前用户的审查历史列表 */
export function getContractList() {
  return http.get('/contracts/list')
}
