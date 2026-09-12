<!--
  AiConsult.vue —— AI法律咨询页面
  功能：
    1. 对话式法律咨询界面（用户右侧气泡 / AI 左侧头像气泡）
    2. 快捷问题标签，一键提问
    3. 调用后端 /api/v1/chat 接口（后端再调用 FastGPT），回复持久化到数据库
    4. 首次发送时自动创建对话，后续消息关联到同一对话
    5. 接收首页搜索框通过路由 query.q 携带的问题并自动发送
    6. 一键清空对话（删除后端对话并重置本地状态）
-->
<script setup>
import { ref, reactive, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Promotion, RefreshLeft, ChatDotRound } from '@element-plus/icons-vue'
// 引入后端对话接口
import {
  createConversation,
  deleteConversation,
  sendMessage as sendMessageApi
} from '@/api/chat'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()
const { isLoggedIn } = useAuth()

/**
 * 消息对象结构
 * @property {'user'|'ai'} role    - 消息发送方
 * @property {string} content      - 消息文本内容
 * @property {string} time         - 发送时间（HH:mm 格式）
 * @property {boolean} [isWelcome] - 标记欢迎语
 * @property {boolean} [isError]   - 标记错误提示
 */
const messages = reactive([
  {
    role: 'ai',
    isWelcome: true,
    content:
      '您好，我是法宝 AI 法律顾问。我可以为您解答婚姻家庭、劳动纠纷、合同债务、房产交通等方面的法律问题，请描述您遇到的情况。',
    time: currentTime()
  }
])

// 输入框内容
const inputText = ref('')
// AI 是否正在生成回复
const isReplying = ref(false)
// 当前对话 ID（后端创建后赋值），null 表示尚未创建对话
const conversationId = ref(null)

const messageListRef = ref(null)

// 快捷问题配置
const quickQuestions = [
  '公司拖欠工资怎么办？',
  '借钱给朋友没有借条能起诉吗？',
  '离婚时房产如何分割？',
  '试用期被辞退有赔偿吗？'
]

/** 获取当前时间 HH:mm */
function currentTime() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(now.getHours())}:${pad(now.getMinutes())}`
}

/** 滚动消息列表到底部 */
const scrollToBottom = async () => {
  await nextTick()
  const el = messageListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

/**
 * 发送一条消息
 * @param {string} [text] - 可选，快捷问题使用
 */
const sendMessage = async (text) => {
  const content = (text ?? inputText.value).trim()
  if (!content || isReplying.value) return

  // 未登录时提示并跳转到登录（通过 header 的弹窗）
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录后再使用法律咨询')
    return
  }

  // 1. 追加用户消息
  messages.push({ role: 'user', content, time: currentTime() })
  inputText.value = ''
  scrollToBottom()

  // 2. 预插入空 AI 消息（显示打字动效）
  const aiMsg = reactive({
    role: 'ai',
    content: '',
    time: currentTime()
  })
  messages.push(aiMsg)
  isReplying.value = true
  scrollToBottom()

  try {
    // 3. 首次发送时创建对话，获取 conversationId
    if (!conversationId.value) {
      const conv = await createConversation(content.slice(0, 30))
      conversationId.value = conv.id
    }

    // 4. 调用后端发送消息接口（后端内部调用 FastGPT，返回完整 AI 回复）
    const res = await sendMessageApi(conversationId.value, content)
    // 5. 填充 AI 回复内容
    aiMsg.content = res.assistant_message.content
  } catch (err) {
    // 请求失败：展示错误信息
    aiMsg.content = '请求失败，请稍后重试。'
    aiMsg.isError = true
  } finally {
    isReplying.value = false
    scrollToBottom()
  }
}

/**
 * 清空对话：删除后端对话记录，重置本地状态
 */
const clearMessages = async () => {
  // 若已创建后端对话，则删除它
  if (conversationId.value) {
    try {
      await deleteConversation(conversationId.value)
    } catch {
      // 删除失败不影响本地重置
    }
  }
  // 重置本地消息与对话 ID
  messages.splice(0, messages.length, {
    role: 'ai',
    isWelcome: true,
    content: '对话已清空，请问您有什么法律问题需要咨询？',
    time: currentTime()
  })
  conversationId.value = null
  ElMessage.success('对话已清空')
}

// 页面挂载时：若首页搜索框携带问题则自动发送
onMounted(() => {
  const q = route.query.q
  if (q) {
    setTimeout(() => sendMessage(String(q)), 300)
  }
})
</script>

<template>
  <div class="consult-page">
    <!-- 页面顶部标题横幅 -->
    <section class="page-hero">
      <div class="container">
        <h1 class="page-hero__title">AI法律咨询</h1>
        <p class="page-hero__desc">智能问答 · 7×24小时在线 · 快速获取专业法律建议</p>
      </div>
    </section>

    <!-- 对话主体区域 -->
    <section class="container chat-section">
      <div class="chat-card">
        <!-- 对话窗口头部 -->
        <div class="chat-header">
          <div class="chat-header__left">
            <el-icon :size="20" color="#c9a96e"><ChatDotRound /></el-icon>
            <span class="chat-header__title">法宝 AI 法律顾问</span>
            <span class="online-badge">在线</span>
          </div>
          <el-button text :icon="RefreshLeft" @click="clearMessages">清空对话</el-button>
        </div>

        <!-- 消息列表区 -->
        <div ref="messageListRef" class="message-list">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message-row"
            :class="msg.role === 'user' ? 'message-row--user' : 'message-row--ai'"
          >
            <div class="avatar avatar--ai" v-if="msg.role === 'ai'">法</div>
            <div class="avatar avatar--user" v-else>我</div>

            <!-- 用户消息气泡 -->
            <div v-if="msg.role === 'user'" class="bubble bubble--user">
              {{ msg.content }}
            </div>

            <!-- AI 消息气泡 -->
            <div v-else class="ai-content">
              <div
                v-if="msg.content"
                class="bubble"
                :class="['bubble--ai', { 'bubble--error': msg.isError }]"
              >
                {{ msg.content }}
              </div>
              <!-- 回复中：打字动效 -->
              <div v-else-if="isReplying" class="bubble bubble--ai typing">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
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
/* 页面顶部横幅 */
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

/* 对话卡片 */
.chat-section {
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

.online-badge {
  font-size: 12px;
  color: #52a86b;
  background-color: rgba(82, 168, 107, 0.1);
  border-radius: 999px;
  padding: 2px 10px;
}

.message-list {
  height: 440px;
  overflow-y: auto;
  padding: 24px 20px;
  background-color: var(--color-bg-light);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.message-row--user {
  flex-direction: row-reverse;
}

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

.bubble {
  max-width: 72%;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.8;
  border-radius: 10px;
  white-space: pre-line;
  word-break: break-word;
}

.bubble--ai {
  background-color: #ffffff;
  color: var(--color-text-main);
  border: 1px solid var(--color-border);
  border-top-left-radius: 2px;
}

.bubble--user {
  background-color: var(--color-primary);
  color: #ffffff;
  border-top-right-radius: 2px;
}

.bubble--error {
  border-color: rgba(229, 83, 61, 0.4);
  background-color: rgba(229, 83, 61, 0.06);
  color: #c0492f;
}

.ai-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  max-width: 72%;
  min-width: 0;
}

.ai-content .bubble {
  max-width: 100%;
}

/* 打字动效 */
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

.chat-tip {
  text-align: center;
  font-size: 12px;
  color: #b4b9c0;
  padding: 10px 0 14px;
}

@media (max-width: 640px) {
  .message-list {
    height: 380px;
  }

  .bubble,
  .ai-content {
    max-width: 82%;
  }
}
</style>
