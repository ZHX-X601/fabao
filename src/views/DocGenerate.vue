<!--
  DocGenerate.vue —— 文书生成页面
  采用三步式流程（el-steps）：
    第一步：选择文书类型（借款合同 / 劳动合同 / 租赁合同 / 民事起诉状）
    第二步：填写文书关键信息（动态表单，字段随文书类型切换）
    第三步：AI 生成中（模拟进度）→ 文书预览，支持重新生成与下载（演示提示）
-->
<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
// 引入图标
import {
  Money,
  Briefcase,
  House,
  Tickets,
  ArrowLeft,
  Download,
  RefreshRight,
  Document
} from '@element-plus/icons-vue'
// 引入后端文书生成接口
import { generateDocument as generateDocumentApi, downloadDocument } from '@/api/document'
import { useAuth } from '@/composables/useAuth'

const { isLoggedIn } = useAuth()

/**
 * 文书类型配置
 * @property {string} key        - 类型唯一标识
 * @property {string} name       - 类型名称
 * @property {string} desc       - 类型说明
 * @property {Component} icon    - 卡片图标
 * @property {Array} fields      - 该类型所需填写的表单字段 { prop,label,type,placeholder }
 */
const docTypes = [
  {
    key: 'loan',
    name: '借款合同',
    desc: '适用于个人/企业间资金借贷',
    icon: Money,
    fields: [
      { prop: 'lender', label: '出借人（甲方）', placeholder: '请输入出借人姓名或单位名称' },
      { prop: 'borrower', label: '借款人（乙方）', placeholder: '请输入借款人姓名或单位名称' },
      { prop: 'amount', label: '借款金额（元）', placeholder: '如：50000' },
      { prop: 'period', label: '借款期限', placeholder: '如：自2026年1月1日至2027年1月1日' },
      { prop: 'rate', label: '约定年利率（%）', placeholder: '如：4（留空则视为无息）' }
    ]
  },
  {
    key: 'labor',
    name: '劳动合同',
    desc: '用人单位与劳动者签订用工合同',
    icon: Briefcase,
    fields: [
      { prop: 'employer', label: '用人单位（甲方）', placeholder: '请输入单位全称' },
      { prop: 'worker', label: '劳动者（乙方）', placeholder: '请输入劳动者姓名' },
      { prop: 'position', label: '工作岗位', placeholder: '如：前端开发工程师' },
      { prop: 'period', label: '合同期限', placeholder: '如：固定期限三年' },
      { prop: 'salary', label: '月工资（元）', placeholder: '如：12000' }
    ]
  },
  {
    key: 'rent',
    name: '租赁合同',
    desc: '房屋、设备等租赁事项约定',
    icon: House,
    fields: [
      { prop: 'lessor', label: '出租方（甲方）', placeholder: '请输入出租方姓名或单位名称' },
      { prop: 'lessee', label: '承租方（乙方）', placeholder: '请输入承租方姓名或单位名称' },
      { prop: 'target', label: '租赁物及地址', placeholder: '如：某市某区某小区1栋201室' },
      { prop: 'rent', label: '月租金（元）', placeholder: '如：3500' },
      { prop: 'period', label: '租赁期限', placeholder: '如：2026年3月1日至2027年3月1日' }
    ]
  },
  {
    key: 'complaint',
    name: '民事起诉状',
    desc: '向法院提起民事诉讼的标准文书',
    icon: Tickets,
    fields: [
      { prop: 'plaintiff', label: '原告信息', placeholder: '姓名、性别、身份证号、住址、联系方式' },
      { prop: 'defendant', label: '被告信息', placeholder: '姓名/单位名称、住址、联系方式' },
      { prop: 'claim', label: '诉讼请求', placeholder: '如：1.判令被告偿还借款5万元；2.本案诉讼费由被告承担' },
      { prop: 'reason', label: '事实与理由', placeholder: '请简要描述纠纷经过' }
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
// 生成进度百分比
const generateProgress = ref(0)
// 生成结果文本
const resultText = ref('')
// 生成定时器引用，便于在重新生成前清理
let progressTimer = null

// 当前文书类型对应的字段列表（供模板动态渲染表单）
const currentFields = computed(() => selectedType.value?.fields ?? [])

/**
 * 第一步：点击文书类型卡片，选中并进入第二步
 * @param {object} type - 被点击的文书类型配置对象
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
  // 未登录提示
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再使用文书生成')
    return
  }

  // 简单非空校验：所有字段都必须填写
  const emptyField = currentFields.value.find((f) => !formData[f.prop]?.trim())
  if (emptyField) {
    ElMessage.warning(`请填写「${emptyField.label}」`)
    return
  }

  activeStep.value = 2
  runGenerate()
}

/**
 * 第三步：播放生成进度动画，进度满后调用后端接口生成文书
 */
const runGenerate = () => {
  generating.value = true
  generateProgress.value = 0
  resultText.value = ''
  clearInterval(progressTimer)

  progressTimer = setInterval(() => {
    generateProgress.value += Math.floor(Math.random() * 12) + 6
    if (generateProgress.value >= 100) {
      generateProgress.value = 100
      clearInterval(progressTimer)
      // 进度满后调用后端文书生成接口
      callBackendGenerate()
    }
  }, 120)
}

/**
 * 调用后端文书生成接口，获取生成的文书全文
 */
const callBackendGenerate = async () => {
  try {
    const res = await generateDocumentApi({
      doc_type: selectedType.value.name,
      form_data: { ...formData }
    })
    resultText.value = res.generated_content
  } catch {
    resultText.value = '文书生成失败，请稍后重试。'
  } finally {
    generating.value = false
  }
}

/**
 * 根据所选文书类型与表单数据拼接完整的模拟文书文本
 * @returns {string} 文书全文
 */
const buildDocument = () => {
  const d = formData
  // 当天日期，作为文书落款日期（演示用）
  const today = new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  // 按类型分别生成文书模板
  switch (selectedType.value.key) {
    case 'loan':
      return `借款合同

甲方（出借人）：${d.lender}
乙方（借款人）：${d.borrower}

一、借款金额
乙方向甲方借款人民币（大写）${toChineseAmount(d.amount)}元整（￥${d.amount}元）。

二、借款期限
${d.period}。

三、借款利息
${d.rate ? `双方约定借款年利率为 ${d.rate}%，利随本清。` : '本借款为无息借款。'}

四、还款方式
乙方应于借款到期日一次性向甲方归还全部借款本金及利息。

五、违约责任
乙方未按期还款的，应按逾期金额每日万分之五向甲方支付违约金。

六、争议解决
本合同履行过程中发生争议，双方应协商解决；协商不成的，可向甲方所在地人民法院提起诉讼。

七、其他
本合同一式两份，甲乙双方各执一份，自双方签字（盖章）之日起生效。

甲方（签字/盖章）：                    乙方（签字/盖章）：

日期：${today}`

    case 'labor':
      return `劳动合同

甲方（用人单位）：${d.employer}
乙方（劳动者）：${d.worker}

根据《中华人民共和国劳动合同法》及相关法律法规，甲乙双方在平等自愿、协商一致的基础上，签订本合同。

一、合同期限
${d.period}。

二、工作岗位与内容
乙方同意根据甲方工作需要，担任${d.position}岗位工作，应按时、保质完成工作任务。

三、劳动报酬
甲方每月以货币形式向乙方支付工资，月工资标准为人民币${d.salary}元，于每月15日前发放。

四、工作时间与休息休假
甲方安排乙方执行标准工时制度，乙方依法享有法定节假日、年休假等休息权利。

五、社会保险
甲方依法为乙方缴纳基本养老、医疗、失业、工伤、生育保险及住房公积金。

六、合同的解除与终止
双方解除、终止劳动合同应依照《劳动合同法》的规定执行，符合条件的甲方应支付经济补偿。

七、争议解决
因履行本合同发生争议，可向劳动争议仲裁委员会申请仲裁。

甲方（盖章）：                          乙方（签字）：

日期：${today}`

    case 'rent':
      return `租赁合同

甲方（出租方）：${d.lessor}
乙方（承租方）：${d.lessee}

根据《中华人民共和国民法典》及相关规定，双方就租赁事宜达成如下协议：

一、租赁物
甲方将位于${d.target}的房屋/设施出租给乙方使用。

二、租赁期限
${d.period}。

三、租金及支付方式
月租金为人民币${d.rent}元，乙方按【月/季】提前支付，首期租金于交付租赁物之日支付。

四、押金
乙方于签约时向甲方支付相当于一个月租金的押金，租赁期满且乙方无违约的，甲方全额无息退还。

五、双方权利义务
甲方保证租赁物权属清晰、可正常使用；乙方应合理使用租赁物，不得擅自转租或改变用途。

六、违约责任
任何一方违约，应向守约方支付相当于一个月租金的违约金；造成损失的，还应承担赔偿责任。

七、争议解决
协商不成的，可向租赁物所在地人民法院起诉。

甲方（签字/盖章）：                    乙方（签字/盖章）：

日期：${today}`

    default:
      return `民事起诉状

原告：${d.plaintiff}

被告：${d.defendant}

诉讼请求：
${d.claim}

事实与理由：
${d.reason}

综上所述，被告的行为已严重损害原告的合法权益。为维护自身合法权益，原告依据《中华人民共和国民事诉讼法》的相关规定，特向贵院提起诉讼，恳请依法判如所请。

此致
XXXX人民法院

具状人（签名）：

${today}`
  }
}

/**
 * 简易金额数字转中文大写（仅做演示，实际项目请使用专业库）
 * @param {string|number} num - 金额数字
 * @returns {string} 中文大写金额
 */
const toChineseAmount = (num) => {
  const n = Number(num)
  if (!n) return '零'
  const digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
  const units = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
  const intPart = Math.floor(n)
  const str = String(intPart)
  let result = ''
  for (let i = 0; i < str.length; i++) {
    const digit = Number(str[i])
    const unit = units[str.length - 1 - i]
    result += digit === 0 ? digits[0] : digits[digit] + unit
  }
  // 简单去重连续的"零"
  return result.replace(/零+/g, '零').replace(/零$/, '')
}

/**
 * 下载文书：调用后端接口生成 Word 文件并触发浏览器下载
 */
const handleDownload = async () => {
  if (!resultText.value) return
  try {
    const blob = await downloadDocument({
      content: resultText.value,
      doc_type: selectedType.value?.name || '文书'
    })
    // 从响应头中提取文件名（后端通过 Content-Disposition 返回）
    // 这里直接用类型 + 时间戳命名
    const timestamp = new Date().toISOString().slice(0, 10)
    const fileName = `${selectedType.value?.name || '文书'}_${timestamp}.docx`
    // 创建临时 URL 并触发下载
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('文书已下载')
  } catch {
    ElMessage.error('下载失败，请稍后重试')
  }
}

/**
 * 重新填写：回到第一步
 */
const restart = () => {
  clearInterval(progressTimer)
  selectedType.value = null
  resultText.value = ''
  generateProgress.value = 0
  activeStep.value = 0
}
</script>

<template>
  <div class="doc-page">
    <!-- ========== 页面顶部横幅 ========== -->
    <section class="page-hero">
      <div class="container">
        <h1 class="page-hero__title">智能文书生成</h1>
        <p class="page-hero__desc">三步生成规范法律文书 · 涵盖合同、诉讼等常用场景</p>
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
          <!-- 图标外框 -->
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
            :label="field.label"
          >
            <el-input
              v-model="formData[field.prop]"
              :placeholder="field.placeholder"
              clearable
            />
          </el-form-item>
        </el-form>

        <!-- 表单操作按钮 -->
        <div class="form-actions">
          <el-button :icon="ArrowLeft" @click="backToType">上一步</el-button>
          <el-button type="primary" class="gold-btn" @click="startGenerate">
            开始生成文书
          </el-button>
        </div>
      </div>

      <!-- 第三步：生成中 / 结果预览 -->
      <div v-else class="result-card">
        <!-- 生成中：进度条 + 提示 -->
        <div v-if="generating" class="generating">
          <el-icon :size="40" color="#c9a96e" class="generating__icon">
            <RefreshRight />
          </el-icon>
          <p class="generating__text">AI 正在为您生成《{{ selectedType.name }}》...</p>
          <el-progress
            :percentage="generateProgress"
            :stroke-width="10"
            color="#c9a96e"
            class="generating__bar"
          />
          <p class="generating__tips">正在匹配标准条款库、校验法律要素</p>
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

          <!-- 文书正文预览（pre 保留换行与空格） -->
          <div class="doc-preview">{{ resultText }}</div>

          <!-- 预览操作按钮 -->
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

/* 步骤条整体留白 */
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

/* 悬停上浮 + 金色描边 */
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

/* 表单标题 */
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

/* 按钮区右对齐 */
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

/* 金色主按钮（与首页 CTA 风格统一） */
.gold-btn {
  background-color: var(--color-gold);
  border-color: var(--color-gold);
}

.gold-btn:hover,
.gold-btn:focus {
  background-color: var(--color-gold-light);
  border-color: var(--color-gold-light);
}

/* ========== 生成中状态 ========== */
.generating {
  text-align: center;
  padding: 48px 0;
}

/* 旋转动画图标 */
.generating__icon {
  animation: spin 1.4s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.generating__text {
  margin: 20px 0 24px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
}

.generating__bar {
  max-width: 420px;
  margin: 0 auto;
}

.generating__tips {
  margin-top: 14px;
  font-size: 13px;
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

/* 文书预览区域：仿纸张样式 */
.doc-preview {
  background-color: #fcfbf7; /* 轻微泛黄纸张色 */
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 36px 40px;
  font-size: 14px;
  line-height: 2.1;
  color: #2b2b2b;
  white-space: pre-wrap; /* 保留换行和连续空格 */
  max-height: 460px;
  overflow-y: auto;
  /* 使用衬线字体增强正式文书的阅读感 */
  font-family: 'SimSun', 'Songti SC', serif;
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
    grid-template-columns: 1fr; /* 窄屏单列 */
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
