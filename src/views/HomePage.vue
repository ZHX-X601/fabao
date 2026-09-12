<!--
  HomePage.vue —— 首页
  页面结构：
    1. Hero 大标题区域：主标题、副标题、搜索框样式的咨询入口、快捷入口标签
    2. 核心功能区域：三张功能卡片（FeatureCard 组件复用）
  配色：深蓝主背景（#1a3a5c）+ 金色点缀（#c9a96e），营造专业法律感
-->
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
// 引入 Element Plus 图标（搜索、对话、文书新增、文书审核）
import { Search, ChatDotRound, DocumentAdd, DocumentChecked } from '@element-plus/icons-vue'
// 引入功能卡片公共组件
import FeatureCard from '@/components/FeatureCard.vue'

const router = useRouter()

// 用户在搜索框中输入的法律问题（双向绑定）
const question = ref('')

/**
 * 三大核心功能卡片配置数据
 * 使用数组驱动渲染，后续新增模块只需在此添加数据即可
 */
const features = [
  {
    icon: ChatDotRound, // 对话气泡图标
    title: 'AI法律咨询',
    description: '智能问答，快速获取法律建议',
    to: '/ai-consult'
  },
  {
    icon: DocumentAdd, // "文档 + 新增"图标
    title: '文书生成',
    description: '一键生成标准法律文书',
    to: '/doc-generate'
  },
  {
    icon: DocumentChecked, // "文档 + 对勾"图标
    title: '合同审查',
    description: '智能识别合同风险条款',
    to: '/contract-review'
  }
]

// 快捷入口标签（与 Hero 搜索框下方的小标签对应）
const quickLinks = [
  { label: '法律咨询', to: '/ai-consult' },
  { label: '合同审查', to: '/contract-review' },
  { label: '文书起草', to: '/doc-generate' }
]

/**
 * 点击"立即咨询"按钮：跳转到 AI 法律咨询页面
 * 若用户输入了问题，则通过路由 query 携带过去，便于咨询页回填（预留能力）
 */
const handleConsult = () => {
  router.push({
    path: '/ai-consult',
    query: question.value.trim() ? { q: question.value.trim() } : {}
  })
}

/**
 * 在输入框按下回车键时触发咨询（提升输入体验）
 */
const handleEnter = () => {
  handleConsult()
}

/**
 * 点击快捷标签：直接跳转到对应功能页
 * @param {string} to - 目标路由路径
 */
const handleQuickLink = (to) => {
  router.push(to)
}
</script>

<template>
  <div class="home-page">
    <!-- ========== Hero 大标题区域 ========== -->
    <section class="hero">
      <!-- 装饰性圆形元素：仅作视觉点缀，不响应交互 -->
      <div class="hero-decoration">
        <span class="circle circle--left"></span>
        <span class="circle circle--center"></span>
        <span class="circle circle--right"></span>
      </div>

      <div class="hero-content container">
        <!-- 主标题："法律助手"四字使用金色高亮 -->
        <h1 class="hero-title">
          您的智能<span class="hero-title--gold">法律助手</span>
        </h1>

        <!-- 副标题 -->
        <p class="hero-subtitle">让法律服务触手可及</p>

        <!-- 搜索框样式的 CTA（行动号召）区域 -->
        <div class="search-box">
          <!-- 搜索图标 -->
          <el-icon class="search-icon"><Search /></el-icon>
          <!-- 问题输入框：回车直接咨询 -->
          <input
            v-model="question"
            class="search-input"
            type="text"
            placeholder="输入您的法律问题，开启 AI 智能咨询..."
            @keyup.enter="handleEnter"
          />
          <!-- 咨询按钮：金色背景 -->
          <el-button class="search-btn" @click="handleConsult">立即咨询</el-button>
        </div>

        <!-- 快捷入口标签组 -->
        <div class="quick-links">
          <span class="quick-links__label">快速开始：</span>
          <button
            v-for="link in quickLinks"
            :key="link.to"
            class="quick-tag"
            type="button"
            @click="handleQuickLink(link.to)"
          >
            {{ link.label }}
          </button>
        </div>
      </div>
    </section>

    <!-- ========== 核心功能区域 ========== -->
    <section class="features">
      <div class="container">
        <!-- 区域标题 -->
        <div class="section-head">
          <h2 class="section-title">核心功能</h2>
          <p class="section-subtitle">专业 AI 技术，助力法律工作提效</p>
          <!-- 标题下方金色装饰短线 -->
          <span class="title-bar"></span>
        </div>

        <!-- 功能卡片区：三列等宽布局，移动端自动换行 -->
        <div class="feature-grid">
          <!-- 遍历 features 配置，复用 FeatureCard 组件渲染三张卡片 -->
          <FeatureCard
            v-for="item in features"
            :key="item.to"
            :icon="item.icon"
            :title="item.title"
            :description="item.description"
            :to="item.to"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ==================== Hero 区域样式 ==================== */

.hero {
  position: relative;
  overflow: hidden; /* 裁掉超出区域的装饰圆 */
  /* 深蓝渐变背景，增强空间层次感 */
  background: linear-gradient(135deg, #0f243a 0%, var(--color-primary) 55%, #2c5680 100%);
  padding: 84px 0 96px;
}

/* 装饰圆形容器：铺满 Hero，不拦截鼠标事件 */
.hero-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

/* 装饰圆通用样式：半透明浅色圆，营造科技氛围 */
.circle {
  position: absolute;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.05);
}

.circle--left {
  width: 220px;
  height: 220px;
  left: -70px;
  bottom: -80px;
}

.circle--center {
  width: 90px;
  height: 90px;
  left: 54%;
  top: 38%;
  background-color: rgba(201, 169, 110, 0.12); /* 金色半透明圆 */
}

.circle--right {
  width: 260px;
  height: 260px;
  right: -90px;
  top: -100px;
}

/* Hero 内容居中 */
.hero-content {
  position: relative;
  z-index: 1; /* 置于装饰圆之上 */
  text-align: center;
}

/* 主标题 */
.hero-title {
  font-size: 40px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 3px;
}

/* 主标题金色高亮部分 */
.hero-title--gold {
  color: var(--color-gold);
}

/* 副标题 */
.hero-subtitle {
  margin-top: 18px;
  font-size: 17px;
  letter-spacing: 6px; /* 字距拉开，庄重有质感 */
  color: rgba(255, 255, 255, 0.8);
}

/* 搜索框：白色胶囊形容器 */
.search-box {
  display: flex;
  align-items: center;
  max-width: 620px;
  margin: 32px auto 0;
  padding: 6px 6px 6px 18px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}

/* 搜索图标颜色 */
.search-icon {
  color: var(--color-text-secondary);
  font-size: 18px;
  flex-shrink: 0;
}

/* 输入框：占满剩余空间，去掉默认边框 */
.search-input {
  flex: 1;
  min-width: 0; /* 防止内容撑破弹性容器 */
  height: 40px;
  margin: 0 12px;
  border: none;
  outline: none;
  font-size: 14px;
  color: var(--color-text-main);
  background: transparent;
}

/* 输入框占位提示文字颜色 */
.search-input::placeholder {
  color: #b4b9c0;
}

/* 金色咨询按钮 */
.search-btn {
  flex-shrink: 0;
  height: 40px;
  padding: 0 26px;
  font-weight: 600;
  color: #ffffff;
  background-color: var(--color-gold);
  border-color: var(--color-gold);
  border-radius: 6px;
}

/* 按钮悬停时金色提亮 */
.search-btn:hover,
.search-btn:focus {
  color: #ffffff;
  background-color: var(--color-gold-light);
  border-color: var(--color-gold-light);
}

/* 快捷入口标签行 */
.quick-links {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.quick-links__label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

/* 快捷标签：描边胶囊按钮 */
.quick-tag {
  padding: 4px 14px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.85);
  background-color: transparent;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 999px; /* 全圆角形成胶囊形 */
  cursor: pointer;
  transition: all 0.2s ease;
}

/* 悬停时标签变为金色描边 */
.quick-tag:hover {
  color: var(--color-gold);
  border-color: var(--color-gold);
}

/* ==================== 核心功能区域样式 ==================== */

.features {
  background-color: var(--color-bg-light);
  padding: 70px 0 90px;
}

/* 区域标题区 */
.section-head {
  text-align: center;
  margin-bottom: 48px;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-primary);
}

.section-subtitle {
  margin-top: 12px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 标题下金色短线 */
.title-bar {
  display: block;
  width: 44px;
  height: 3px;
  margin: 16px auto 0;
  background-color: var(--color-gold);
  border-radius: 2px;
}

/* 三列卡片网格布局 */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
  max-width: 1040px;
  margin: 0 auto;
}

/* ==================== 响应式适配 ==================== */

/* 平板：卡片改为两列 */
@media (max-width: 900px) {
  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 手机：卡片单列排列，缩小 Hero 字号 */
@media (max-width: 640px) {
  .hero {
    padding: 60px 0 70px;
  }

  .hero-title {
    font-size: 28px;
    letter-spacing: 2px;
  }

  .hero-subtitle {
    font-size: 14px;
    letter-spacing: 3px;
  }

  /* 搜索框纵向排列输入框与按钮 */
  .search-box {
    flex-direction: column;
    gap: 10px;
    padding: 14px;
  }

  .search-input {
    width: 100%;
    margin: 0;
    text-align: center;
  }

  .search-btn {
    width: 100%;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
