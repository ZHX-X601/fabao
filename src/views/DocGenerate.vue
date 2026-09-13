<!--
  DocGenerate.vue —— 文书生成页面
  采用三步式流程（el-steps）：
    第一步：选择文书类型（民事起诉状 / 民事答辩状 / 律师函 / 授权委托书）
    第二步：填写文书关键信息（动态表单，字段随文书类型切换）
    第三步：AI 生成中（模拟进度）→ 文书预览，支持重新生成与下载
-->
<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
// 引入图标
import {
  Tickets,
  EditPen,
  Message,
  Stamp,
  ArrowLeft,
  Download,
  RefreshRight,
  Document,
  Loading,
  CircleCheckFilled
} from '@element-plus/icons-vue'
// 引入后端文书生成接口
import { generateDocument as generateDocumentApi, downloadDocument } from '@/api/document'
import { useAuth } from '@/composables/useAuth'

const { isLoggedIn } = useAuth()

/**
 * 文书类型配置
 * @property {string} key        - 类型唯一标识
 * @property {string} name       - 类型名称（与 FastGPT 提示词和后端 DOC_TYPES 一致）
 * @property {string} desc       - 类型说明
 * @property {Component} icon    - 卡片图标
 * @property {Array} fields      - 该类型所需填写的表单字段 { prop, label, type, placeholder }
 *   type: 'input' 单行输入 | 'textarea' 多行输入
 */
const docTypes = [
  {
    key: 'complaint',
    name: '民事起诉状',
    desc: '向法院提起民事诉讼的标准文书',
    icon: Tickets,
    fields: [
      { prop: 'plaintiff', label: '原告信息', type: 'input', placeholder: '姓名、身份证号、联系电话、住址' },
      { prop: 'defendant', label: '被告信息', type: 'input', placeholder: '姓名/单位名称、身份证号、住址、联系方式' },
      { prop: 'claims', label: '诉讼请求', type: 'textarea', placeholder: '如：1.判令被告偿还借款5万元及利息；2.本案诉讼费由被告承担' },
      { prop: 'facts', label: '事实与理由', type: 'textarea', placeholder: '请简要描述纠纷经过与理由' },
      { prop: 'evidence', label: '证据清单', type: 'textarea', placeholder: '如：1.借条一份；2.银行转账记录；3.微信聊天截图', required: false },
      { prop: 'court', label: '此致法院', type: 'input', placeholder: '如：北京市朝阳区人民法院', required: false }
    ]
  },
  {
    key: 'defense',
    name: '民事答辩状',
    desc: '针对起诉状提交的答辩文书',
    icon: EditPen,
    fields: [
      { prop: 'respondent', label: '答辩人信息', type: 'input', placeholder: '姓名、身份证号、联系电话、住址' },
      { prop: 'opponent', label: '被答辩人信息', type: 'input', placeholder: '姓名/单位名称、住址、联系方式' },
      { prop: 'opinion', label: '答辩意见', type: 'textarea', placeholder: '如：答辩人不同意原告的全部诉讼请求' },
      { prop: 'defense_facts', label: '事实与理由', type: 'textarea', placeholder: '请逐条阐述答辩的事实依据和理由' },
      { prop: 'conclusion', label: '答辩结论', type: 'textarea', placeholder: '如：请求法院依法驳回原告的全部诉讼请求', required: false },
      { prop: 'court', label: '此致法院', type: 'input', placeholder: '如：北京市朝阳区人民法院', required: false }
    ]
  },
  {
    key: 'lawyer_letter',
    name: '律师函',
    desc: '律师代表委托人发出的正式函件',
    icon: Message,
    fields: [
      { prop: 'recipient', label: '致函对象', type: 'input', placeholder: '如：XX公司法定代表人张三' },
      { prop: 'lawyer', label: '发函律师', type: 'input', placeholder: '如：李四律师' },
      { prop: 'law_firm', label: '律师事务所', type: 'input', placeholder: '如：XX律师事务所' },
      { prop: 'statement', label: '事实陈述', type: 'textarea', placeholder: '请客观描述相关事实经过' },
      { prop: 'legal_opinion', label: '法律意见', type: 'textarea', placeholder: '如：根据《民法典》相关规定，贵方行为已构成违约' },
      { prop: 'demand', label: '郑重函告要求', type: 'textarea', placeholder: '如：请贵方在收函后7日内支付全部欠款' },
      { prop: 'deadline', label: '履行期限', type: 'input', placeholder: '如：收到本函之日起7个工作日内', required: false }
    ]
  },
  {
    key: 'authorization',
    name: '授权委托书',
    desc: '委托他人代为办理法律事务',
    icon: Stamp,
    fields: [
      { prop: 'principal', label: '委托人', type: 'input', placeholder: '姓名/单位名称、身份证号' },
      { prop: 'agent', label: '受委托人', type: 'input', placeholder: '姓名、身份证号、联系电话' },
      { prop: 'matter', label: '委托事项', type: 'textarea', placeholder: '如：代为办理XX房屋买卖合同签署及产权过户相关事宜' },
      { prop: 'authority', label: '代理权限', type: 'input', placeholder: '一般代理 / 特别授权（请注明具体权限）' },
      { prop: 'valid_period', label: '有效期', type: 'input', placeholder: '如：自2026年1月1日至2026年12月31日' }
    ]
  }
]

// 当前步骤：0 选择类型 / 1 填写信息 / 2 生成预览
const activeStep = ref(0)
// 当前选中的文书类型对象
const selectedType = ref(null)
// 表单数据对象（key 为字段 prop，value 为用户输入）
const formData = reactive({})
// 是否正在生成（控制生成动画与按钮禁用）
const generating = ref(false)
// 生成结果：结构化 JSON 对象 {title, sections: [{type, ...}, ...]}
const resultData = ref(null)

// ========== 阶段骨架提示 ==========
// 不再用百分比进度条（无法预估等待时间易误判为卡顿），
// 改用阶段清单 + 当前激活项旋转图标，给用户"系统在分步思考"的连续感受。
const stageTexts = [
  '正在理解您提供的案件信息',
  '正在检索相关法律法规与司法实践',
  '正在构建文书框架与格式规范',
  '正在生成文书全文'
]
const currentStageIdx = ref(0)
let stageTimer = null

// 当前文书类型对应的字段列表（供模板动态渲染表单）
const currentFields = computed(() => selectedType.value?.fields ?? [])

/** 统一清理定时器（避免切换步骤/卸载时还在跑） */
const clearTimers = () => {
  if (stageTimer) {
    clearInterval(stageTimer)
    stageTimer = null
  }
}

onBeforeUnmount(clearTimers)

/**
 * 第一步：点击文书类型卡片，选中并进入第二步
 */
const selectType = (type) => {
  selectedType.value = type
  // 清空上一次可能残留的表单数据
  Object.keys(formData).forEach((k) => delete formData[k])
  activeStep.value = 1
}

/**
 * 第二步：返回第一步重新选择文书类型
 */
const backToType = () => {
  activeStep.value = 0
}

/**
 * 第二步：校验必填项后进入第三步并触发生成
 */
const startGenerate = () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再使用文书生成')
    return
  }

  // 校验必填字段（required 未设为 false 的字段）
  const emptyField = currentFields.value.find(
    (f) => f.required !== false && !formData[f.prop]?.trim()
  )
  if (emptyField) {
    ElMessage.warning(`请填写「${emptyField.label}」`)
    return
  }

  activeStep.value = 2
  runGenerate()
}

/**
 * 第三步：调用后端生成文书，期间用阶段骨架提示呈现思考过程
 *
 * 流程：启动阶段定时器（每 2.5 秒切换到下一阶段，覆盖常见 5-15s 等待窗口） ->
 * 立即调用真实 API -> 后端返回后清掉定时器、跳转结果页
 *
 * 注意：阶段切换不再依赖"百分比"，避免"100% 后卡住"的负面体验
 */
const runGenerate = () => {
  generating.value = true
  currentStageIdx.value = 0
  resultData.value = null
  clearTimers()

  // 阶段推进定时器（每 2.5 秒切到下一阶段，最后阶段停留直到 API 返回）
  stageTimer = setInterval(() => {
    if (currentStageIdx.value < stageTexts.length - 1) {
      currentStageIdx.value++
    }
  }, 2500)

  callBackendGenerate()
}

/**
 * 调用后端文书生成接口，获取结构化 JSON 文书
 */
const callBackendGenerate = async () => {
  try {
    const res = await generateDocumentApi({
      doc_type: selectedType.value.name,
      form_data: { ...formData }
    })
    // 后端返回的 generated_content 是 JSON 字符串，解析为对象
    const content = res.generated_content
    if (typeof content === 'string') {
      try {
        resultData.value = JSON.parse(content)
      } catch {
        // 解析失败，包装为简单 paragraph
        resultData.value = { title: selectedType.value.name, sections: [{ type: 'paragraph', content }] }
      }
    } else if (typeof content === 'object' && content !== null) {
      resultData.value = content
    } else {
      resultData.value = null
    }
  } catch {
    resultData.value = { title: selectedType.value.name, sections: [{ type: 'notice', content: '文书生成失败，请稍后重试。' }] }
  } finally {
    generating.value = false
    clearTimers()
  }
}

/**
 * 下载文书：将结构化 JSON 传给后端，后端按 section type 确定性排版生成 docx
 */
const handleDownload = async () => {
  if (!resultData.value) return
  try {
    const blob = await downloadDocument({
      doc_data: JSON.stringify(resultData.value),
      doc_type: selectedType.value?.name || '文书'
    })
    if (!(blob instanceof Blob)) {
      ElMessage.error('返回数据格式异常，请稍后重试')
      return
    }

    const filename = `${selectedType.value?.name || '文书'}.docx`
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    setTimeout(() => window.URL.revokeObjectURL(url), 100)
    ElMessage.success('文书已下载')
  } catch {
    ElMessage.error('下载失败，请稍后重试')
  }
}

/**
 * 重新填写：回到第一步
 */
const restart = () => {
  clearTimers()
  selectedType.value = null
  resultData.value = null
  currentStageIdx.value = 0
  activeStep.value = 0
}
</script>

<template>
  <div class="doc-page">
    <!-- ========== 页面顶部横幅 ========== -->
    <section class="page-hero">
      <div class="container">
        <h1 class="page-hero__title">智能文书生成</h1>
        <p class="page-hero__desc">三步生成规范法律文书 · AI 起草 · 涵盖诉讼、函件、委托等场景</p>
      </div>
    </section>

    <!-- ========== 步骤条 + 内容区 ========== -->
    <section class="container doc-section">
      <!-- 步骤指示条 -->
      <el-steps :active="activeStep" align-center class="doc-steps">
        <el-step title="选择类型" description="选择需要的文书" />
        <el-step title="填写信息" description="补充关键条款信息" />
        <el-step title="生成预览" description="AI 一键生成文书" />
      </el-steps>

      <!-- 第一步：文书类型选择卡片 -->
      <div v-if="activeStep === 0" class="type-grid">
        <div
          v-for="type in docTypes"
          :key="type.key"
          class="type-card"
          @click="selectType(type)"
        >
          <div class="type-card__icon">
            <el-icon :size="26"><component :is="type.icon" /></el-icon>
          </div>
          <h3 class="type-card__name">{{ type.name }}</h3>
          <p class="type-card__desc">{{ type.desc }}</p>
          <span class="type-card__action">选择并填写 →</span>
        </div>
      </div>

      <!-- 第二步：动态信息表单 -->
      <div v-else-if="activeStep === 1" class="form-card">
        <h2 class="form-card__title">
          <el-icon><Document /></el-icon>
          {{ selectedType.name }} · 信息填写
        </h2>

        <el-form label-position="top" class="doc-form">
          <el-form-item
            v-for="field in currentFields"
            :key="field.prop"
            :label="field.label + (field.required === false ? '（选填）' : '')"
          >
            <el-input
              v-if="field.type !== 'textarea'"
              v-model="formData[field.prop]"
              :placeholder="field.placeholder"
              clearable
            />
            <el-input
              v-else
              v-model="formData[field.prop]"
              type="textarea"
              :rows="3"
              :placeholder="field.placeholder"
            />
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <el-button :icon="ArrowLeft" @click="backToType">上一步</el-button>
          <el-button type="primary" class="gold-btn" @click="startGenerate">
            开始生成文书
          </el-button>
        </div>
      </div>

      <!-- 第三步：生成中 / 结果预览 -->
      <div v-else class="result-card">
        <!-- 生成中：阶段骨架提示（不用百分比进度条，避免"100% 后卡住"误判） -->
        <div v-if="generating" class="generating">
          <div class="generating__spinner">
            <div class="generating__spinner-ring"></div>
            <el-icon :size="32" color="#c9a96e">
              <Document />
            </el-icon>
          </div>
          <p class="generating__title">AI 正在为您生成《{{ selectedType.name }}》</p>

          <!-- 阶段清单：已完成 / 进行中 / 待办 三态 -->
          <div class="generating__stages">
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

          <p class="generating__tips">复杂文书生成约需 5-15 秒，请耐心等候</p>
        </div>

        <!-- 生成完成：文书预览 -->
        <template v-else>
          <div class="result-head">
            <div>
              <h2 class="result-title">《{{ selectedType.name }}》已生成</h2>
              <p class="result-subtitle">请仔细核对文书内容，确认无误后可下载使用</p>
            </div>
            <el-tag type="success" size="large" effect="light">生成成功</el-tag>
          </div>

          <div class="doc-preview">
            <!-- 标题 -->
            <div class="doc-preview__title">{{ resultData.title }}</div>
            <!-- sections 渲染 -->
            <template v-for="(sec, idx) in resultData.sections" :key="idx">
              <!-- 当事人信息：标签加粗 -->
              <div v-if="sec.type === 'party'" class="doc-preview__party">
                <strong>{{ sec.role }}：</strong>{{ sec.content }}
              </div>
              <!-- 节标题 -->
              <div v-else-if="sec.type === 'heading'" class="doc-preview__heading">
                {{ sec.content }}
              </div>
              <!-- 编号列表项 -->
              <div v-else-if="sec.type === 'numbered'" class="doc-preview__numbered">
                <strong>{{ sec.number }}、</strong>{{ sec.content }}
              </div>
              <!-- 正文段落 -->
              <div v-else-if="sec.type === 'paragraph'" class="doc-preview__paragraph">
                {{ sec.content }}
              </div>
              <!-- 居中行 -->
              <div v-else-if="sec.type === 'center'" class="doc-preview__center" :class="{ 'doc-preview__center--bold': sec.bold }">
                {{ sec.content }}
              </div>
              <!-- 落款 -->
              <div v-else-if="sec.type === 'signature'" class="doc-preview__signature">
                {{ sec.content }}
              </div>
              <!-- 空行 -->
              <div v-else-if="sec.type === 'blank'" class="doc-preview__blank"></div>
              <!-- 提示信息 -->
              <div v-else-if="sec.type === 'notice'" class="doc-preview__notice">
                {{ sec.content }}
              </div>
            </template>
          </div>

          <div class="result-actions">
            <el-button :icon="RefreshRight" @click="runGenerate">重新生成</el-button>
            <el-button :icon="ArrowLeft" @click="backToType">修改信息</el-button>
            <el-button :icon="Download" type="primary" class="gold-btn" @click="handleDownload">
              下载文书
            </el-button>
            <el-button text @click="restart">再写一份</el-button>
          </div>

          <p class="result-tip">
            提示：AI 生成文书仅供参考，正式签署前建议请执业律师审核，以规避法律风险。
          </p>
        </template>
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
.doc-section {
  padding: 36px 20px 64px;
  max-width: 1000px;
}

.doc-steps {
  margin-bottom: 40px;
}

/* 第一步：类型卡片网格（两列） */
.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.type-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 32px 28px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.type-card:hover {
  transform: translateY(-5px);
  border-color: var(--color-gold);
  box-shadow: 0 12px 28px rgba(26, 58, 92, 0.12);
}

.type-card__icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background-color: var(--color-primary);
  border: 2px solid var(--color-gold);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.type-card__name {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.type-card__desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 16px;
}

.type-card__action {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-gold);
}

/* ========== 第二、三步卡片通用 ========== */
.form-card,
.result-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 32px 36px;
  box-shadow: 0 6px 20px rgba(26, 58, 92, 0.06);
}

.form-card__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  color: var(--color-primary);
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

/* 两列表单 */
.doc-form {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  column-gap: 24px;
}

/* textarea 占满整行 */
.doc-form :deep(.el-form-item:has(textarea)) {
  grid-column: 1 / -1;
}

.form-actions,
.result-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.form-actions {
  justify-content: flex-end;
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

/* ========== 生成中状态（阶段骨架提示） ========== */
.generating {
  text-align: center;
  padding: 48px 0;
}

/* 双层环形旋转图标：外圈旋转 + 中心静态图标 */
.generating__spinner {
  position: relative;
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.generating__spinner-ring {
  position: absolute;
  inset: 0;
  border: 3px solid transparent;
  border-top-color: #c9a96e;
  border-right-color: rgba(201, 169, 110, 0.5);
  border-radius: 50%;
  animation: spin 1.1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.generating__title {
  margin: 0 0 28px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
}

/* 阶段清单 */
.generating__stages {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 380px;
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

.generating__tips {
  margin-top: 22px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* ========== 生成结果 ========== */
.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.result-title {
  font-size: 18px;
  color: var(--color-primary);
}

.result-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.doc-preview {
  background-color: #fcfbf7;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 36px 40px;
  font-size: 14px;
  line-height: 2;
  color: #2b2b2b;
  max-height: 460px;
  overflow-y: auto;
  font-family: 'SimSun', 'Songti SC', serif;
}

.doc-preview__title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: #1a3a5c;
  margin-bottom: 24px;
  font-family: 'Microsoft YaHei', sans-serif;
}

.doc-preview__party {
  text-indent: 2em;
  margin-bottom: 4px;
}

.doc-preview__heading {
  font-size: 15px;
  font-weight: 700;
  color: #1a3a5c;
  margin-top: 14px;
  margin-bottom: 8px;
  font-family: 'Microsoft YaHei', sans-serif;
}

.doc-preview__numbered {
  text-indent: 2em;
  margin-bottom: 4px;
}

.doc-preview__paragraph {
  text-indent: 2em;
  margin-bottom: 4px;
}

.doc-preview__center {
  text-align: center;
  margin-bottom: 4px;
}

.doc-preview__center--bold {
  font-weight: 700;
}

.doc-preview__signature {
  text-align: right;
  margin-top: 6px;
  margin-bottom: 4px;
}

.doc-preview__blank {
  height: 1em;
}

.doc-preview__notice {
  text-indent: 2em;
  font-style: italic;
  color: #6b6b6b;
  font-size: 13px;
  margin-top: 12px;
}

.result-actions {
  margin-top: 24px;
  flex-wrap: wrap;
}

.result-tip {
  margin-top: 16px;
  font-size: 12px;
  color: #b4b9c0;
}

/* ========== 响应式 ========== */
@media (max-width: 720px) {
  .type-grid,
  .doc-form {
    grid-template-columns: 1fr;
  }

  .form-card,
  .result-card {
    padding: 24px 20px;
  }

  .doc-preview {
    padding: 24px 20px;
  }
}
</style>
