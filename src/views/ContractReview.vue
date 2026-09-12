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
// 引入图标：上传、危险警告、对勾、信息、重新上传、下载报告、文档勾选
import {
  UploadFilled,
  WarningFilled,
  CircleCheckFilled,
  InfoFilled,
  RefreshLeft,
  Download,
  DocumentChecked
} from '@element-plus/icons-vue'

// 当前页面阶段：upload（上传）/ analyzing（分析中）/ report（报告）
const phase = ref('upload')

// 已上传的文件名（用于报告头部展示）
const fileName = ref('')
// 分析进度 0-100
const analyzeProgress = ref(0)
// 当前分析阶段提示文案
const analyzeStage = ref('')

/**
 * 风险报告模拟数据（实际项目中应来自后端 AI 审查接口）
 * level：风险等级 high 高风险 / medium 中风险 / low 低风险
 */
const report = reactive({
  score: 78, // 综合评分（满分 100）
  conclusion:
    '本合同整体框架完整，但存在 2 处高风险条款可能导致您方承担过重责任，建议在签署前与对方协商修改。',
  // 各等级风险数量
  counts: { high: 2, medium: 2, low: 1 },
  risks: [
    {
      level: 'high',
      title: '违约责任严重不对等',
      clause:
        '第八条：乙方违约应向甲方支付合同总金额 30% 的违约金；甲方违约的，仅需赔偿乙方实际直接损失。',
      analysis:
        '该条款单方面加重了乙方责任，违约金比例过高且甲方违约责任缺失，属于明显不对等条款。根据《民法典》第五百八十五条，约定违约金过分高于实际损失的，违约方可请求法院或仲裁机构予以适当减少。',
      suggestion:
        '建议将双方违约金比例统一（如均为合同总金额的 10%-20%），并增加甲方逾期履约时对等的违约责任。'
    },
    {
      level: 'high',
      title: '争议解决方式约定不利',
      clause: '第十二条：因本合同产生的一切争议，由甲方所在地人民法院管辖。',
      analysis:
        '管辖法院仅约定甲方所在地，一旦发生争议，乙方需赴异地诉讼，维权成本显著增加。',
      suggestion:
        '建议修改为"由被告所在地或合同履行地人民法院管辖"，或约定提交中立的仲裁委员会仲裁。'
    },
    {
      level: 'medium',
      title: '付款时间与方式约定不明',
      clause: '第五条：甲方应在项目验收合格后及时支付尾款。',
      analysis:
        '"及时"未明确具体期限，"验收合格"也未约定验收期限与标准，容易成为甲方拖延付款的借口。',
      suggestion:
        '建议明确为"验收合格后 7 个工作日内一次性支付"，并补充"甲方收到验收申请后 5 日内未提出异议视为验收合格"。'
    },
    {
      level: 'medium',
      title: '知识产权归属存在空白',
      clause: '合同未对乙方交付成果的知识产权归属、使用许可范围作出约定。',
      analysis:
        '委托开发/设计类成果如未约定权属，易在后续使用、二次开发中产生知识产权纠纷。',
      suggestion:
        '建议增加条款：明确成果知识产权归属方、使用范围，以及背景知识产权的许可方式。'
    },
    {
      level: 'low',
      title: '缺少送达条款',
      clause: '合同首部列明了双方地址，但未约定该地址作为法律文书送达地址。',
      analysis:
        '缺少送达地址确认条款，诉讼阶段可能因送达难导致案件周期拉长。',
      suggestion:
        '建议补充："双方确认合同载明地址为各类通知及诉讼文书的送达地址，拒收或退回视为送达。"'
    }
  ],
  // 审查中识别出的合规/完善条款，给用户正向反馈
  passed: [
    '合同主体信息完整，名称与落款一致',
    '合同标的、数量、质量标准约定明确',
    '保密条款内容规范、期限合理'
  ]
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
 * 文件选择回调（el-upload 设置 :auto-upload="false" 后通过 on-change 触发）
 * @param {object} uploadFile - Element Plus 上传文件对象
 */
const handleFileChange = (uploadFile) => {
  const file = uploadFile.raw
  if (!file) return

  // 校验文件类型：仅支持常见文档格式
  const allowedExt = /\.(doc|docx|pdf|txt|wps)$/i
  if (!allowedExt.test(file.name)) {
    ElMessage.error('仅支持 Word、PDF、TXT、WPS 格式的合同文件')
    return
  }

  // 校验文件大小：限制 20MB 以内
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 20MB')
    return
  }

  fileName.value = file.name
  startAnalyze()
}

/**
 * 开始模拟 AI 分析：进度递增并切换阶段文案，满进度后进入报告页
 */
const startAnalyze = () => {
  phase.value = 'analyzing'
  analyzeProgress.value = 0
  analyzeStage.value = stageTexts[0]
  clearInterval(analyzeTimer)

  analyzeTimer = setInterval(() => {
    analyzeProgress.value += Math.floor(Math.random() * 8) + 4

    // 根据进度区间切换阶段提示
    const idx = Math.min(
      stageTexts.length - 1,
      Math.floor((analyzeProgress.value / 100) * stageTexts.length)
    )
    analyzeStage.value = stageTexts[idx]

    if (analyzeProgress.value >= 100) {
      analyzeProgress.value = 100
      clearInterval(analyzeTimer)
      // 稍作停顿后展示报告，让"100%"被看到
      setTimeout(() => {
        phase.value = 'report'
      }, 500)
    }
  }, 180)
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
