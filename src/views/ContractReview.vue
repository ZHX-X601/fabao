<!--
  ContractReview.vue —— 合同审查页面
  页面状态流转（phase）：
    upload    上传合同文件（el-upload 拖拽/点击，仅做前端演示，不真实上传）
    analyzing AI 分析中（进度条 + 分阶段提示）
    report    审查报告：综合评分、风险等级统计、风险条款逐条分析与修改建议
  支持"重新审查"回到上传状态
-->
<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
// 引入图标
import {
  UploadFilled,
  WarningFilled,
  CircleCheckFilled,
  InfoFilled,
  RefreshLeft,
  Download,
  DocumentChecked
} from '@element-plus/icons-vue'
// 引入后端合同审查接口
import { uploadContract, reviewContract } from '@/api/contract'
import { useAuth } from '@/composables/useAuth'

const { isLoggedIn } = useAuth()

// 当前页面阶段：upload（上传）/ analyzing（分析中）/ report（报告）
const phase = ref('upload')

// 已上传的文件名
const fileName = ref('')
// 后端返回的合同记录 ID（审查时需要）
const contractId = ref(null)
// 分析进度 0-100
const analyzeProgress = ref(0)
// 当前分析阶段提示文案
const analyzeStage = ref('')

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

// 分析阶段的提示文案（随进度推进切换）
const stageTexts = [
  '正在解析合同文本...',
  '识别合同主体与关键条款...',
  '比对法律法规与风险规则库...',
  '评估条款风险等级...',
  '生成审查报告与修改建议...'
]

// 分析过程定时器引用
let analyzeTimer = null

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
 * 开始审查：播放进度动画，进度满后调用后端审查接口
 */
const startAnalyze = () => {
  phase.value = 'analyzing'
  analyzeProgress.value = 0
  analyzeStage.value = stageTexts[0]
  clearInterval(analyzeTimer)

  analyzeTimer = setInterval(() => {
    analyzeProgress.value += Math.floor(Math.random() * 8) + 4

    const idx = Math.min(
      stageTexts.length - 1,
      Math.floor((analyzeProgress.value / 100) * stageTexts.length)
    )
    analyzeStage.value = stageTexts[idx]

    if (analyzeProgress.value >= 100) {
      analyzeProgress.value = 100
      clearInterval(analyzeTimer)
      // 进度满后调用后端审查接口
      callBackendReview()
    }
  }, 180)
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
    // 稍作停顿后展示报告
    setTimeout(() => {
      phase.value = 'report'
    }, 300)
  } catch {
    phase.value = 'upload'
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
 * 下载报告：演示环境仅给出提示
 */
const handleDownloadReport = () => {
  ElMessage.success('正式环境将在此处下载审查报告（Word/PDF）')
}

/**
 * 重新审查：清空文件并回到上传状态
 */
const resetAll = () => {
  clearInterval(analyzeTimer)
  fileName.value = ''
  contractId.value = null
  analyzeProgress.value = 0
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
          accept=".doc,.docx,.pdf,.txt,.wps"
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
        <p class="upload-tip">演示说明：上传任意符合格式的文件即可查看模拟审查报告</p>
      </div>

      <!-- ========== 阶段二：分析中 ========== -->
      <div v-else-if="phase === 'analyzing'" class="analyzing-card">
        <el-icon :size="46" color="#c9a96e" class="analyzing-icon">
          <DocumentChecked />
        </el-icon>
        <h2 class="analyzing-title">正在审查《{{ fileName }}》</h2>
        <el-progress
          :percentage="analyzeProgress"
          :stroke-width="12"
          color="#c9a96e"
          class="analyzing-bar"
        />
        <p class="analyzing-stage">{{ analyzeStage }}</p>
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
        </div>

        <!-- 合规条款（正向反馈） -->
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

        <!-- 报告操作按钮 -->
        <div class="report-actions">
          <el-button :icon="RefreshLeft" @click="resetAll">重新审查</el-button>
          <el-button type="primary" class="gold-btn" :icon="Download" @click="handleDownloadReport">
            下载完整报告
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

/* ========== 分析中卡片 ========== */
.analyzing-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 64px 40px;
  text-align: center;
  box-shadow: 0 6px 20px rgba(26, 58, 92, 0.06);
}

/* 文档图标轻微呼吸动画 */
.analyzing-icon {
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

.analyzing-title {
  margin: 22px 0 28px;
  font-size: 17px;
  color: var(--color-primary);
  /* 文件名过长时省略 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analyzing-bar {
  max-width: 460px;
  margin: 0 auto;
}

.analyzing-stage {
  margin-top: 16px;
  font-size: 13px;
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
