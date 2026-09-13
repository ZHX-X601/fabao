<!--
  ContractReview.vue —— 合同审查页面
  页面状态流转（phase）：
    upload    上传合同文件（el-upload 拖拽/点击，仅做前端演示，不真实上传）
    analyzing AI 分析中（进度条 + 分阶段提示）
    report    审查报告：综合评分、风险等级统计、风险条款逐条分析与修改建议
  支持"重新审查"回到上传状态
-->
<script setup>
import { ref, reactive, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
// 引入图标
import {
  UploadFilled,
  WarningFilled,
  CircleCheckFilled,
  InfoFilled,
  RefreshLeft,
  Download,
  DocumentChecked,
  Loading
} from '@element-plus/icons-vue'
// 引入后端合同审查接口
import { uploadContract, reviewContract, downloadContractReport } from '@/api/contract'
import { useAuth } from '@/composables/useAuth'

const { isLoggedIn } = useAuth()

// 当前页面阶段：upload（上传）/ analyzing（分析中）/ report（报告）
const phase = ref('upload')

// 已上传的文件名
const fileName = ref('')
// 后端返回的合同记录 ID（审查时需要）
const contractId = ref(null)
// 下载状态：'idle' | 'downloading'
const downloading = ref(false)

/**
 * 风险报告数据（来自后端审查结果）
 * level：风险等级 high 高风险 / medium 中风险 / low 低风险
 */
const report = reactive({
  score: 0,
  conclusion: '',
  counts: { high: 0, medium: 0, low: 0 },
  risks: [],
  passed: []
})

// ========== 阶段骨架提示 ==========
// 不再用百分比进度条（无法预估等待时间易误判为卡顿），
// 改用阶段清单 + 当前激活项旋转图标，给用户"系统在分步思考"的连续感受。
const stageTexts = [
  '正在解析合同文本',
  '识别合同主体与关键条款',
  '比对法律法规与风险规则库',
  '评估条款风险等级',
  '生成审查报告与修改建议'
]
const currentStageIdx = ref(0)
let stageTimer = null

/** 统一清理定时器 */
const clearTimers = () => {
  if (stageTimer) {
    clearInterval(stageTimer)
    stageTimer = null
  }
}

onBeforeUnmount(clearTimers)

/**
 * 文件选择回调：上传到后端提取文本，然后开始审查
 * @param {object} uploadFile - Element Plus 上传文件对象
 */
const handleFileChange = async (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return

  // 未登录提示
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再使用合同审查')
    return
  }

  // 校验文件类型
  const allowedExt = /\.(doc|docx|pdf|txt|wps)$/i
  if (!allowedExt.test(file.name)) {
    ElMessage.error('仅支持 Word、PDF、TXT、WPS 格式的合同文件')
    return
  }

  // 校验文件大小
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 20MB')
    return
  }

  fileName.value = file.name

  // 上传文件到后端（后端提取文本并创建审查记录）
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await uploadContract(formData)
    contractId.value = res.id
    // 上传成功后开始审查（播放进度动画 + 调用审查接口）
    startAnalyze()
  } catch {
    // 错误已在 http.js 中提示
  }
}

/**
 * 开始审查：进入 analyzing 阶段，启动阶段骨架提示，立即调用审查接口
 *
 * 阶段切换：每 2 秒推进一项（5 项 ≈ 10 秒，覆盖常见 5-15s 审查时间），
 * 真实 API 一旦返回立刻跳到报告页，避免"100% 后卡住"的负面体验。
 */
const startAnalyze = () => {
  phase.value = 'analyzing'
  currentStageIdx.value = 0
  clearTimers()

  stageTimer = setInterval(() => {
    if (currentStageIdx.value < stageTexts.length - 1) {
      currentStageIdx.value++
    }
  }, 2000)

  callBackendReview()
}

/**
 * 调用后端合同审查接口，将结果填充到 report
 */
const callBackendReview = async () => {
  try {
    const res = await reviewContract(contractId.value)
    const result = res.review_result
    if (result) {
      report.score = result.score || 0
      report.conclusion = result.conclusion || ''
      report.counts = result.counts || { high: 0, medium: 0, low: 0 }
      report.risks = result.risks || []
      report.passed = result.passed || []
    }
    // 稍作停顿后展示报告（让最后一个阶段动画播放完成）
    setTimeout(() => {
      phase.value = 'report'
    }, 300)
  } catch {
    phase.value = 'upload'
  } finally {
    clearTimers()
  }
}

/**
 * 风险等级配置映射：标签文字、标签类型、主题色
 * @param {string} level - high/medium/low
 */
const levelMap = {
  high: { label: '高风险', type: 'danger', color: '#e5533d' },
  medium: { label: '中风险', type: 'warning', color: '#e6a23c' },
  low: { label: '低风险', type: 'info', color: '#909399' }
}

/**
 * 评分对应的结论颜色（分数越低越偏红）
 */
const getScoreColor = (score) => {
  if (score >= 85) return '#52a86b'
  if (score >= 70) return '#e6a23c'
  return '#e5533d'
}

/**
 * 下载完整报告：从后端生成 .docx 文件并触发浏览器下载
 *
 * 流程：调用 downloadContractReport(contractId) 拿 Blob ->
 * 从响应头 Content-Disposition 解析文件名（兼容中文）->
 * 用 a[download] 触发浏览器下载
 */
const handleDownloadReport = async () => {
  if (!contractId.value) {
    ElMessage.warning('暂无审查结果可下载')
    return
  }
  if (downloading.value) return // 防重复点击
  downloading.value = true
  const loading = ElMessage.info({ message: '正在生成报告...', duration: 0 })
  try {
    // 直接拿 Blob（http.js 已对 responseType=blob 做短路）
    const blob = await downloadContractReport(contractId.value)
    if (!(blob instanceof Blob)) {
      ElMessage.error('返回数据格式异常，请稍后重试')
      return
    }

    // 从 Content-Disposition 头解析文件名（后端返回 RFC 5987 编码的中文名）
    const dispo = (blob && blob._responseHeaders?.['content-disposition']) || ''
    const utf8Match = dispo.match(/filename\*=UTF-8''([^;]+)/i)
    let filename = '合同审查报告.docx'
    if (utf8Match) {
      try {
        filename = decodeURIComponent(utf8Match[1])
      } catch {
        // 解析失败就用默认名
      }
    } else {
      const asciiMatch = dispo.match(/filename="([^"]+)"/i)
      if (asciiMatch) filename = asciiMatch[1]
    }

    // 创建临时链接并触发下载
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    // 立即释放 URL，避免内存泄漏
    setTimeout(() => URL.revokeObjectURL(url), 100)

    ElMessage.success(`报告已下载：${filename}`)
  } catch (err) {
    // 错误已在 http.js 拦截器中提示
    console.error('下载报告失败：', err)
  } finally {
    loading.close()
    downloading.value = false
  }
}

/**
 * 重新审查：清空文件并回到上传状态
 */
const resetAll = () => {
  clearTimers()
  fileName.value = ''
  contractId.value = null
  currentStageIdx.value = 0
  phase.value = 'upload'
}
</script>

<template>
  <div class="review-page">
    <!-- ========== 页面顶部横幅 ========== -->
    <section class="page-hero">
      <div class="container">
        <h1 class="page-hero__title">智能合同审查</h1>
        <p class="page-hero__desc">上传合同文件 · AI 逐条识别风险条款 · 提供专业修改建议</p>
      </div>
    </section>

    <section class="container review-section">
      <!-- ========== 阶段一：文件上传 ========== -->
      <div v-if="phase === 'upload'" class="upload-card">
        <!-- el-upload 关闭自动上传，由 on-change 接管做前端演示 -->
        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="false"
          accept=".doc,.docx,.pdf,.txt,.wps,.text"
          :on-change="handleFileChange"
          class="upload-dragger"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">将合同文件拖拽到此处，或<em>点击上传</em></div>
          <div class="upload-hint">支持 DOC / DOCX / PDF / TXT / WPS 格式，文件不超过 20MB</div>
        </el-upload>

        <!-- 能力说明标签 -->
        <div class="upload-features">
          <span class="feature-item">
            <el-icon color="#c9a96e"><CircleCheckFilled /></el-icon>
            风险条款识别
          </span>
          <span class="feature-item">
            <el-icon color="#c9a96e"><CircleCheckFilled /></el-icon>
            权责对等分析
          </span>
          <span class="feature-item">
            <el-icon color="#c9a96e"><CircleCheckFilled /></el-icon>
            修改建议生成
          </span>
          <span class="feature-item">
            <el-icon color="#c9a96e"><CircleCheckFilled /></el-icon>
            法条依据引用
          </span>
        </div>

        <!-- 示例提示 -->
        <p class="upload-tip">上传合同文件，AI 将逐条识别风险条款并提供修改建议</p>
      </div>

      <!-- ========== 阶段二：分析中（阶段骨架提示） ========== -->
      <div v-else-if="phase === 'analyzing'" class="analyzing-card">
        <div class="analyzing-spinner">
          <div class="analyzing-spinner-ring"></div>
          <el-icon :size="40" color="#c9a96e">
            <DocumentChecked />
          </el-icon>
        </div>
        <h2 class="analyzing-title">正在审查《{{ fileName }}》</h2>

        <!-- 阶段清单：已完成 / 进行中 / 待办 三态 -->
        <div class="analyzing-stages">
          <div
            v-for="(stage, idx) in stageTexts"
            :key="idx"
            class="stage-item"
            :class="{
              'stage-item--done': idx < currentStageIdx,
              'stage-item--active': idx === currentStageIdx,
              'stage-item--pending': idx > currentStageIdx
            }"
          >
            <span class="stage-item__icon-wrap">
              <el-icon
                v-if="idx < currentStageIdx"
                class="stage-item__icon"
                color="#52a86b"
              >
                <CircleCheckFilled />
              </el-icon>
              <el-icon
                v-else-if="idx === currentStageIdx"
                class="stage-item__icon stage-item__icon--loading"
                color="#c9a96e"
              >
                <Loading />
              </el-icon>
              <span v-else class="stage-item__dot"></span>
            </span>
            <span class="stage-item__text">{{ stage }}</span>
          </div>
        </div>

        <p class="analyzing-extra">复杂合同审查约需 5-20 秒，请耐心等候</p>
      </div>

      <!-- ========== 阶段三：审查报告 ========== -->
      <div v-else class="report-wrap">
        <!-- 报告概览卡片 -->
        <div class="report-overview">
          <!-- 左侧：综合评分圆环 -->
          <div class="score-area">
            <el-progress
              type="dashboard"
              :percentage="report.score"
              :color="getScoreColor(report.score)"
              :width="130"
              :stroke-width="12"
            />
            <p class="score-label">综合评分</p>
          </div>

          <!-- 右侧：文件名、结论、风险数量统计 -->
          <div class="overview-main">
            <div class="overview-file">
              <el-icon :size="18"><DocumentChecked /></el-icon>
              <span class="overview-filename" :title="fileName">{{ fileName }}</span>
            </div>
            <p class="overview-conclusion">{{ report.conclusion }}</p>

            <!-- 风险等级数量统计 -->
            <div class="level-summary">
              <span class="level-chip level-chip--high">
                <el-icon><WarningFilled /></el-icon>
                高风险 {{ report.counts.high }} 项
              </span>
              <span class="level-chip level-chip--medium">
                <el-icon><WarningFilled /></el-icon>
                中风险 {{ report.counts.medium }} 项
              </span>
              <span class="level-chip level-chip--low">
                <el-icon><InfoFilled /></el-icon>
                低风险 {{ report.counts.low }} 项
              </span>
            </div>
          </div>
        </div>

        <!-- 风险条款列表 -->
        <h2 class="block-title">
          <el-icon color="#c9a96e"><WarningFilled /></el-icon>
          风险条款明细（共 {{ report.risks.length }} 项）
        </h2>

        <div
          v-for="(risk, index) in report.risks"
          :key="index"
          class="risk-card"
          :class="`risk-card--${risk.level}`"
        >
          <!-- 卡片头部：序号 + 标题 + 风险等级标签 -->
          <div class="risk-head">
            <div class="risk-head__left">
              <span class="risk-index">{{ index + 1 }}</span>
              <span class="risk-title">{{ risk.title }}</span>
            </div>
            <el-tag :type="levelMap[risk.level].type" effect="dark" size="small">
              {{ levelMap[risk.level].label }}
            </el-tag>
          </div>

          <!-- 原始条款摘录 -->
          <div class="risk-block">
            <p class="risk-block__label">原文摘录</p>
            <p class="risk-clause">{{ risk.clause }}</p>
          </div>

          <!-- 风险分析 -->
          <div class="risk-block">
            <p class="risk-block__label">风险分析</p>
            <p class="risk-analysis">{{ risk.analysis }}</p>
          </div>

          <!-- 修改建议 -->
          <div class="risk-block risk-block--suggest">
            <p class="risk-block__label">
              <el-icon><CircleCheckFilled /></el-icon>
              修改建议
            </p>
            <p class="risk-suggestion">{{ risk.suggestion }}</p>
          </div>

          <!-- 法律依据 -->
          <div v-if="risk.law" class="risk-block">
            <p class="risk-block__label">
              <el-icon><InfoFilled /></el-icon>
              法律依据
            </p>
            <p class="risk-law">{{ risk.law }}</p>
          </div>
        </div>

        <!-- 合规条款（正向反馈，有内容时才显示） -->
        <template v-if="report.passed && report.passed.length">
          <h2 class="block-title block-title--pass">
            <el-icon color="#52a86b"><CircleCheckFilled /></el-icon>
            合规条款
          </h2>
          <div class="passed-card">
            <div v-for="(item, index) in report.passed" :key="index" class="passed-item">
              <el-icon color="#52a86b"><CircleCheckFilled /></el-icon>
              <span>{{ item }}</span>
            </div>
          </div>
        </template>

        <!-- 报告操作按钮 -->
        <div class="report-actions">
          <el-button :icon="RefreshLeft" @click="resetAll">重新审查</el-button>
          <el-button
            type="primary"
            class="gold-btn"
            :icon="Download"
            :loading="downloading"
            @click="handleDownloadReport"
          >
            {{ downloading ? '生成中...' : '下载完整报告' }}
          </el-button>
        </div>

        <p class="report-tip">审查结果由 AI 生成，仅供参考，不替代律师的专业审查意见。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ========== 页面顶部横幅 ========== */
.page-hero {
  background: linear-gradient(135deg, #0f243a 0%, var(--color-primary) 60%, #2c5680 100%);
  padding: 48px 0;
  text-align: center;
}

.page-hero__title {
  font-size: 30px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 2px;
}

.page-hero__desc {
  margin-top: 12px;
  font-size: 14px;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.75);
}

/* ========== 内容区 ========== */
.review-section {
  padding: 36px 20px 64px;
  max-width: 960px;
}

/* ========== 上传卡片 ========== */
.upload-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 6px 20px rgba(26, 58, 92, 0.06);
}

/* 拖拽上传区：虚线边框 */
.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  padding: 48px 20px;
  border: 2px dashed #c8d3de;
  border-radius: 10px;
  background-color: #fbfcfd;
  transition: border-color 0.2s ease;
}

/* 悬停时边框变金色 */
.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: var(--color-gold);
}

.upload-icon {
  font-size: 52px;
  color: var(--color-primary);
}

.upload-text {
  margin-top: 14px;
  font-size: 15px;
  color: var(--color-text-main);
}

.upload-text em {
  color: var(--color-gold);
  font-style: normal;
  font-weight: 600;
}

.upload-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 能力说明标签行 */
.upload-features {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 28px;
  margin-top: 32px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--color-primary);
}

.upload-tip {
  margin-top: 24px;
  text-align: center;
  font-size: 12px;
  color: #b4b9c0;
}

/* ========== 分析中卡片（阶段骨架提示） ========== */
.analyzing-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 56px 40px;
  text-align: center;
  box-shadow: 0 6px 20px rgba(26, 58, 92, 0.06);
}

/* 双层环形旋转图标：外圈旋转 + 中心静态图标 */
.analyzing-spinner {
  position: relative;
  width: 72px;
  height: 72px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.analyzing-spinner-ring {
  position: absolute;
  inset: 0;
  border: 3px solid transparent;
  border-top-color: #c9a96e;
  border-right-color: rgba(201, 169, 110, 0.5);
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.analyzing-title {
  margin: 0 0 28px;
  font-size: 17px;
  color: var(--color-primary);
  /* 文件名过长时省略 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 580px;
  margin-left: auto;
  margin-right: auto;
}

/* 阶段清单 */
.analyzing-stages {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 400px;
  margin: 0 auto;
  padding: 22px 26px;
  background-color: #fcfbf7;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  text-align: left;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 10px;
  transition: opacity 0.3s ease, color 0.3s ease;
}

/* 待办阶段：置灰、降低存在感 */
.stage-item--pending {
  opacity: 0.45;
}

/* 进行中：加粗、强调颜色 */
.stage-item--active .stage-item__text {
  color: var(--color-primary);
  font-weight: 600;
}

/* 已完成：默认绿色对勾 */
.stage-item__icon {
  font-size: 18px;
}

/* 进行中图标：旋转动画 */
.stage-item__icon--loading {
  animation: spin 1.4s linear infinite;
}

/* 待办阶段的小圆点占位 */
.stage-item__icon-wrap {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stage-item__dot {
  width: 8px;
  height: 8px;
  background-color: #c8d3de;
  border-radius: 50%;
  display: inline-block;
}

.stage-item__text {
  font-size: 14px;
  color: var(--color-text-main);
}

.stage-item--pending .stage-item__text {
  color: #909399;
}

.analyzing-extra {
  margin-top: 22px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* ========== 报告概览 ========== */
.report-overview {
  display: flex;
  align-items: center;
  gap: 36px;
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--color-gold); /* 左侧金色强调边 */
  border-radius: 12px;
  padding: 28px 32px;
  box-shadow: 0 6px 20px rgba(26, 58, 92, 0.06);
}

.score-area {
  text-align: center;
  flex-shrink: 0;
}

.score-label {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.overview-main {
  flex: 1;
  min-width: 0;
}

.overview-file {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-primary);
}

.overview-filename {
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overview-conclusion {
  margin: 12px 0 16px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-main);
}

/* 风险等级统计胶囊 */
.level-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.level-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  padding: 5px 14px;
  border-radius: 999px;
}

.level-chip--high {
  color: #e5533d;
  background-color: rgba(229, 83, 61, 0.1);
}

.level-chip--medium {
  color: #b8821f;
  background-color: rgba(230, 162, 60, 0.12);
}

.level-chip--low {
  color: #909399;
  background-color: rgba(144, 147, 153, 0.12);
}

/* ========== 区块标题 ========== */
.block-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  color: var(--color-primary);
  margin: 36px 0 16px;
}

/* ========== 风险条款卡片 ========== */
.risk-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 22px 24px;
  margin-bottom: 16px;
  box-shadow: 0 3px 12px rgba(26, 58, 92, 0.05);
}

/* 高风险卡片左侧红色强调边，其余用浅金 */
.risk-card--high {
  border-left: 4px solid #e5533d;
}

.risk-card--medium {
  border-left: 4px solid #e6a23c;
}

.risk-card--low {
  border-left: 4px solid #b4b9c0;
}

.risk-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.risk-head__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 风险序号圆形徽标 */
.risk-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--color-primary);
  color: #ffffff;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.risk-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary);
}

/* 条款内容区块 */
.risk-block {
  margin-top: 12px;
}

.risk-block__label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

/* 原文摘录：引用样式（浅灰底 + 竖线） */
.risk-clause {
  font-size: 13.5px;
  line-height: 1.8;
  color: #555;
  background-color: var(--color-bg-light);
  border-left: 3px solid #c8d3de;
  border-radius: 0 6px 6px 0;
  padding: 10px 14px;
}

.risk-analysis {
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--color-text-main);
}

/* 修改建议：浅绿底色，正向引导 */
.risk-block--suggest .risk-suggestion {
  font-size: 13.5px;
  line-height: 1.8;
  color: #2f6b43;
  background-color: rgba(82, 168, 107, 0.08);
  border-left: 3px solid #52a86b;
  border-radius: 0 6px 6px 0;
  padding: 10px 14px;
}

/* 法律依据：浅蓝底色 */
.risk-law {
  font-size: 13px;
  line-height: 1.8;
  color: #3a6b9f;
  background-color: rgba(58, 107, 159, 0.06);
  border-left: 3px solid #3a6b9f;
  border-radius: 0 6px 6px 0;
  padding: 10px 14px;
}

/* ========== 合规条款卡片 ========== */
.passed-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 18px 24px;
}

.passed-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-main);
  line-height: 2;
}

/* ========== 报告操作区 ========== */
.report-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-top: 36px;
}

.gold-btn {
  background-color: var(--color-gold);
  border-color: var(--color-gold);
}

.gold-btn:hover,
.gold-btn:focus {
  background-color: var(--color-gold-light);
  border-color: var(--color-gold-light);
}

.report-tip {
  margin-top: 18px;
  text-align: center;
  font-size: 12px;
  color: #b4b9c0;
}

/* ========== 响应式 ========== */
@media (max-width: 720px) {
  .upload-card {
    padding: 24px 18px;
  }

  /* 概览卡片在窄屏下纵向排列 */
  .report-overview {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }

  .overview-file,
  .level-summary {
    justify-content: center;
  }
}
</style>
