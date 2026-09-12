<!--
  AiConsult.vue —— AI法律咨询页面
  功能：
    1. 对话式法律咨询界面（用户右侧气泡 / AI 左侧头像气泡）
    2. 快捷问题标签，一键提问
    3. AI "正在输入"动效 + 模拟智能回复（当前为本地规则匹配的演示数据）
    4. 接收首页搜索框通过路由 query.q 携带的问题并自动发送
    5. 一键清空对话
-->
<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
// 引入页面所需图标
import {
  Promotion, // 发送按钮（纸飞机）
  RefreshLeft, // 清空对话（向左刷新）
  ChatDotRound // AI 头像气泡
} from '@element-plus/icons-vue'

const route = useRoute()

/**
 * 消息对象结构
 * @property {'user'|'ai'} role    - 消息发送方
 * @property {string} content      - 消息文本内容
 * @property {string} time         - 发送时间（HH:mm 格式）
 */
const messages = reactive([
  // 初始欢迎消息
  {
    role: 'ai',
    content:
      '您好，我是法宝 AI 法律顾问。我可以为您解答婚姻家庭、劳动纠纷、合同债务、房产交通等方面的法律问题，请描述您遇到的情况。',
    time: currentTime()
  }
])

// 输入框内容（双向绑定）
const inputText = ref('')
// AI 是否正在生成回复（控制"正在输入"动画与发送按钮禁用）
const isReplying = ref(false)

// 消息列表容器的引用，用于发送后自动滚动到底部
const messageListRef = ref(null)

// 快捷问题配置：点击标签即可快速提问
const quickQuestions = [
  '公司拖欠工资怎么办？',
  '借钱给朋友没有借条能起诉吗？',
  '离婚时房产如何分割？',
  '试用期被辞退有赔偿吗？'
]

/**
 * 关键词 → 模拟回复库（演示用，实际项目应替换为后端 AI 接口请求）
 * 命中任一关键词即返回对应回复，否则返回通用回复
 */
const replyRules = [
  {
    keywords: ['工资', '拖欠', '劳动', '辞退', '试用期', '赔偿'],
    reply:
      '根据《劳动合同法》相关规定，为您初步分析：\n1. 用人单位应按时足额支付工资，拖欠工资可向当地劳动监察大队投诉；\n2. 也可向劳动争议仲裁委员会申请劳动仲裁，仲裁时效一般为一年；\n3. 请保留劳动合同、工资条、考勤记录、聊天记录等证据；\n4. 若因拖欠工资离职，还可主张经济补偿金。\n建议先与单位协商，协商不成再走法律程序。'
  },
  {
    keywords: ['借', '欠款', '借条', '债务', '起诉'],
    reply:
      '针对民间借贷纠纷，建议如下：\n1. 即使没有借条，转账记录、聊天记录、通话录音、证人证言等也可作为证据；\n2. 可先通过微信、短信等书面方式催款并固定对方承认借款的证据；\n3. 协商不成可向被告住所地或您（接收货币一方）所在地法院起诉；\n4. 诉讼时效为三年，请注意保留催款记录以中断时效。\n金额较大时建议咨询专业律师。'
  },
  {
    keywords: ['离婚', '房产', '分割', '夫妻', '婚姻'],
    reply:
      '关于离婚财产分割，依据《民法典》婚姻家庭编：\n1. 夫妻共同财产原则上均等分割，会适当照顾子女、女方和无过错方；\n2. 婚后购买的房产一般属于共同财产；婚前一方贷款购买、婚后共同还贷的，另一方可就共同还贷及增值部分获得补偿；\n3. 协议离婚需经过三十天离婚冷静期；\n4. 建议梳理房产登记、出资证明、贷款记录等材料。\n涉及房产、抚养权的情形较复杂，建议进一步咨询律师。'
  }
]

// 未命中关键词时的通用回复
const defaultReply =
  '感谢您的描述。根据现有信息，初步建议：\n1. 先固定并保存好相关证据（合同、付款凭证、聊天记录、录音等）；\n2. 优先通过协商解决，协商过程注意留痕；\n3. 协商不成可通过调解、仲裁或诉讼途径维权；\n4. 全国法律服务热线可拨打 12348。\n以上为 AI 生成的参考意见，不构成正式法律意见，复杂问题请咨询执业律师。'

/**
 * 获取当前时间的 HH:mm 字符串
 * @returns {string} 格式化后的时间
 */
function currentTime() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(now.getHours())}:${pad(now.getMinutes())}`
}

/**
 * 将消息列表滚动到底部（在 DOM 更新后执行）
 */
const scrollToBottom = async () => {
  await nextTick()
  const el = messageListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

/**
 * 发送一条用户消息并触发 AI 回复
 * @param {string} [text] - 可选，直接指定发送内容（快捷问题使用）
 */
const sendMessage = (text) => {
  // 优先取参数，其次取输入框；去除首尾空白
  const content = (text ?? inputText.value).trim()

  // 空内容或 AI 回复中则忽略
  if (!content || isReplying.value) return

  // 1. 追加用户消息
  messages.push({ role: 'user', content, time: currentTime() })
  inputText.value = ''
  scrollToBottom()

  // 2. 模拟网络延迟后生成 AI 回复
  isReplying.value = true
  setTimeout(() => {
    const rule = replyRules.find((r) => r.keywords.some((k) => content.includes(k)))
    messages.push({
      role: 'ai',
      content: rule ? rule.reply : defaultReply,
      time: currentTime()
    })
    isReplying.value = false
    scrollToBottom()
  }, 900)
}

/**
 * 清空当前对话，恢复为仅含欢迎消息的状态
 */
const clearMessages = () => {
  messages.splice(0, messages.length, {
    role: 'ai',
    content: '对话已清空，请问您有什么法律问题需要咨询？',
    time: currentTime()
  })
  ElMessage.success('对话已清空')
}

// 页面挂载时：若首页搜索框携带了问题（query.q），则自动发送
onMounted(() => {
  const q = route.query.q
  if (q) {
    setTimeout(() => sendMessage(String(q)), 300)
  }
})
</script>

<template>
  <div class="consult-page">
    <!-- ========== 页面顶部标题横幅 ========== -->
    <section class="page-hero">
      <div class="container">
        <h1 class="page-hero__title">AI法律咨询</h1>
        <p class="page-hero__desc">智能问答 · 7×24小时在线 · 快速获取专业法律建议</p>
      </div>
    </section>

    <!-- ========== 对话主体区域 ========== -->
    <section class="container chat-section">
      <div class="chat-card">
        <!-- 对话窗口头部：标题 + 清空按钮 -->
        <div class="chat-header">
          <div class="chat-header__left">
            <el-icon :size="20" color="#c9a96e"><ChatDotRound /></el-icon>
            <span class="chat-header__title">法宝 AI 法律顾问</span>
            <!-- 在线状态标识 -->
            <span class="online-badge">在线</span>
          </div>
          <el-button text :icon="RefreshLeft" @click="clearMessages">清空对话</el-button>
        </div>

        <!-- 消息列表区：超出高度后内部滚动 -->
        <div ref="messageListRef" class="message-list">
          <!-- 遍历消息，按 role 区分左右气泡样式 -->
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-row"
            :class="msg.role === 'user' ? 'message-row--user' : 'message-row--ai'"
          >
            <!-- AI 头像（用户消息不显示头像，保留占位对齐） -->
            <div class="avatar avatar--ai" v-if="msg.role === 'ai'">法</div>
            <div class="avatar avatar--user" v-else>我</div>

            <!-- 气泡内容：white-space: pre-line 让回复中的换行正常展示 -->
            <div class="bubble" :class="`bubble--${msg.role}`">{{ msg.content }}</div>
          </div>

          <!-- AI 正在输入动效（三个跳动的小圆点） -->
          <div v-if="isReplying" class="message-row message-row--ai">
            <div class="avatar avatar--ai">法</div>
            <div class="bubble bubble--ai typing">
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
              <span class="typing-dot"></span>
            </div>
          </div>
        </div>

        <!-- 快捷问题区 -->
        <div class="quick-area">
          <span class="quick-area__label">常见问题：</span>
          <button
            v-for="q in quickQuestions"
            :key="q"
            type="button"
            class="quick-question"
            :disabled="isReplying"
            @click="sendMessage(q)"
          >
            {{ q }}
          </button>
        </div>

        <!-- 输入发送区 -->
        <div class="input-area">
          <el-input
            v-model="inputText"
            class="input-box"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="请输入您的法律问题，按 Enter 发送，Shift + Enter 换行"
            @keydown.enter.exact.prevent="sendMessage()"
          />
          <!-- 发送按钮：AI 回复中时禁用 -->
          <el-button
            type="primary"
            class="send-btn"
            :icon="Promotion"
            :loading="isReplying"
            @click="sendMessage()"
          >
            发送
          </el-button>
        </div>

        <!-- 底部免责提示 -->
        <p class="chat-tip">AI 回复内容仅供参考，不构成正式法律意见，紧急情况请拨打 12348</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ========== 页面顶部横幅（与其他功能页保持统一风格） ========== */
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

/* ========== 对话卡片 ========== */
.chat-section {
  /* 上下留白，让卡片悬浮在浅灰背景上 */
  padding: 36px 20px 56px;
}

.chat-card {
  max-width: 860px;
  margin: 0 auto;
  background-color: #ffffff;
  border-radius: 12px;
  border: 1px solid var(--color-border);
  box-shadow: 0 6px 20px rgba(26, 58, 92, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 对话窗口头部 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--color-border);
  background-color: #fbfcfd;
}

.chat-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-header__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
}

/* 绿色"在线"小胶囊 */
.online-badge {
  font-size: 12px;
  color: #52a86b;
  background-color: rgba(82, 168, 107, 0.1);
  border-radius: 999px;
  padding: 2px 10px;
}

/* 消息列表：固定高度内部滚动 */
.message-list {
  height: 440px;
  overflow-y: auto;
  padding: 24px 20px;
  background-color: var(--color-bg-light);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 单条消息行 */
.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

/* 用户消息靠右排列 */
.message-row--user {
  flex-direction: row-reverse;
}

/* 头像：深蓝（AI）/ 金色（用户）圆形 */
.avatar {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.avatar--ai {
  background-color: var(--color-primary);
}

.avatar--user {
  background-color: var(--color-gold);
}

/* 气泡通用样式 */
.bubble {
  max-width: 72%;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.8;
  border-radius: 10px;
  white-space: pre-line; /* 保留回复文本中的换行 */
  word-break: break-word;
}

/* AI 气泡：白底深色字 */
.bubble--ai {
  background-color: #ffffff;
  color: var(--color-text-main);
  border: 1px solid var(--color-border);
  border-top-left-radius: 2px; /* 左上角收尖，指向头像 */
}

/* 用户气泡：深蓝底白字 */
.bubble--user {
  background-color: var(--color-primary);
  color: #ffffff;
  border-top-right-radius: 2px; /* 右上角收尖 */
}

/* "正在输入"动效：三个圆点依次跳动 */
.typing {
  display: inline-flex;
  gap: 5px;
  padding: 16px;
}

.typing-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: var(--color-text-secondary);
  animation: typing-bounce 1.2s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing-bounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

/* 快捷问题区 */
.quick-area {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--color-border);
}

.quick-area__label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 快捷问题标签：浅蓝底描边胶囊 */
.quick-question {
  padding: 5px 14px;
  font-size: 13px;
  color: var(--color-primary);
  background-color: rgba(26, 58, 92, 0.05);
  border: 1px solid rgba(26, 58, 92, 0.15);
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-question:hover:not(:disabled) {
  color: #ffffff;
  background-color: var(--color-primary);
  border-color: var(--color-primary);
}

.quick-question:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 输入发送区 */
.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  padding: 14px 20px 6px;
}

.input-box {
  flex: 1;
}

/* 金色发送按钮 */
.send-btn {
  flex-shrink: 0;
  height: 40px;
  background-color: var(--color-gold);
  border-color: var(--color-gold);
}

.send-btn:hover,
.send-btn:focus {
  background-color: var(--color-gold-light);
  border-color: var(--color-gold-light);
}

/* 底部免责提示 */
.chat-tip {
  text-align: center;
  font-size: 12px;
  color: #b4b9c0;
  padding: 10px 0 14px;
}

/* 窄屏适配：气泡占更大宽度 */
@media (max-width: 640px) {
  .message-list {
    height: 380px;
  }

  .bubble {
    max-width: 82%;
  }
}
</style>
