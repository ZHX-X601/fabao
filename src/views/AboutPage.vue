<!--
  AboutPage.vue —— 关于页
  内容：项目简介、核心功能一览、技术栈说明、免责声明
  说明：当前为简单占位内容，后续可在此补充团队介绍、发展历程等
-->
<script setup>
// 引入三个核心功能图标，与首页卡片保持一致
import { ChatDotRound, DocumentAdd, DocumentChecked } from '@element-plus/icons-vue'

/**
 * 核心功能简介数据（与首页三大模块对应，复用同一套图标）
 */
const features = [
  {
    icon: ChatDotRound,
    title: 'AI法律咨询',
    desc: '通过对话式交互，快速获取常见法律问题的初步分析与建议。'
  },
  {
    icon: DocumentAdd,
    title: '文书生成',
    desc: '填写关键信息，一键生成借款合同、劳动合同、起诉状等标准文书。'
  },
  {
    icon: DocumentChecked,
    title: '合同审查',
    desc: '上传合同文件，AI 逐条识别风险条款并给出专业修改建议。'
  }
]

/**
 * 技术栈列表（展示项目所用前后端技术，后续可按实际演进更新）
 */
const techStacks = [
  'Vue 3（Composition API + <script setup>）',
  'Vue Router 4',
  'Element Plus',
  'Vite'
]
</script>

<template>
  <div class="about-page">
    <!-- ========== 页面顶部横幅（与功能页统一风格） ========== -->
    <section class="page-hero">
      <div class="container">
        <h1 class="page-hero__title">关于法宝</h1>
        <p class="page-hero__desc">让法律服务触手可及 · 用技术降低普通人获取法律帮助的门槛</p>
      </div>
    </section>

    <section class="container about-section">
      <!-- ========== 项目简介卡片 ========== -->
      <div class="about-card">
        <h2 class="about-card__title">项目简介</h2>
        <p class="about-card__text">
          「法宝 - AI法律助手」是一个面向普通用户与法律从业者的智能法律服务平台。
          围绕"咨询、文书、审查"三大高频法律场景，借助人工智能技术提供快捷、
          易用的辅助工具，帮助用户在遇到法律问题时快速理清思路、获取参考建议。
        </p>
        <p class="about-card__text">
          项目当前处于持续开发阶段，页面与功能将以演示数据为主，正式能力正在逐步接入中。
        </p>
      </div>

      <!-- ========== 核心功能一览 ========== -->
      <div class="about-card">
        <h2 class="about-card__title">核心功能</h2>
        <div class="feature-list">
          <div v-for="item in features" :key="item.title" class="feature-row">
            <!-- 功能图标：深蓝圆底 + 金色描边，延续全站视觉语言 -->
            <div class="feature-icon">
              <el-icon :size="20" color="#ffffff">
                <component :is="item.icon" />
              </el-icon>
            </div>
            <div class="feature-info">
              <h3 class="feature-name">{{ item.title }}</h3>
              <p class="feature-desc">{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ========== 技术栈说明 ========== -->
      <div class="about-card">
        <h2 class="about-card__title">技术栈</h2>
        <div class="tech-tags">
          <span v-for="tech in techStacks" :key="tech" class="tech-tag">{{ tech }}</span>
        </div>
      </div>

      <!-- ========== 免责声明 ========== -->
      <div class="about-card about-card--disclaimer">
        <h2 class="about-card__title">免责声明</h2>
        <p class="about-card__text">
          本平台由 AI 生成的全部法律内容（包括咨询回复、文书模板、审查报告等）仅供参考与学习，
          不构成正式法律意见。如遇实际法律问题，请咨询持有执业资格的专业律师。
        </p>
      </div>

      <!-- 补充内容占位提示 -->
      <p class="about-more-tip">更多内容（团队介绍、联系方式、发展历程等）持续补充中...</p>
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
.about-section {
  padding: 36px 20px 64px;
  max-width: 860px;
}

/* 内容卡片通用样式 */
.about-card {
  background-color: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 28px 32px;
  margin-bottom: 20px;
  box-shadow: 0 6px 20px rgba(26, 58, 92, 0.06);
}

/* 卡片标题：左侧金色竖条装饰 */
.about-card__title {
  position: relative;
  font-size: 18px;
  color: var(--color-primary);
  padding-left: 12px;
  margin-bottom: 16px;
}

.about-card__title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  border-radius: 2px;
  background-color: var(--color-gold);
}

/* 简介正文 */
.about-card__text {
  font-size: 14px;
  line-height: 2;
  color: var(--color-text-main);
}

/* 免责声明卡片：浅灰底弱化显示 */
.about-card--disclaimer {
  background-color: var(--color-bg-light);
}

.about-card--disclaimer .about-card__text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* ========== 核心功能列表 ========== */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.feature-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

/* 图标外框：与首页 FeatureCard 一致的深蓝圆底 + 金色描边 */
.feature-icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background-color: var(--color-primary);
  border: 2px solid var(--color-gold);
  display: flex;
  align-items: center;
  justify-content: center;
}

.feature-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 4px;
}

.feature-desc {
  font-size: 13px;
  line-height: 1.8;
  color: var(--color-text-secondary);
}

/* ========== 技术栈标签 ========== */
.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tech-tag {
  padding: 6px 16px;
  font-size: 13px;
  color: var(--color-primary);
  background-color: rgba(26, 58, 92, 0.05);
  border: 1px solid rgba(26, 58, 92, 0.15);
  border-radius: 999px;
}

/* 补充内容占位提示 */
.about-more-tip {
  text-align: center;
  font-size: 12px;
  color: #b4b9c0;
  margin-top: 8px;
}

/* 窄屏适配：减小卡片内边距 */
@media (max-width: 640px) {
  .about-card {
    padding: 22px 20px;
  }
}
</style>
