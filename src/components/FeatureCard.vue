<!--
  FeatureCard.vue —— 功能卡片公共组件
  首页三个功能模块（AI法律咨询 / 文书生成 / 合同审查）复用同一卡片结构，
  通过 props 传入图标、标题、描述和跳转路径来区分内容。
-->
<script setup>
import { useRouter } from 'vue-router'
// 引入按钮中使用的箭头图标（Element Plus 图标库）
import { ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

/**
 * 组件属性定义
 * @property {Component} icon     - 卡片顶部展示的图标组件（来自 @element-plus/icons-vue）
 * @property {string} title       - 功能模块名称
 * @property {string} description - 功能简短描述
 * @property {string} to          - 点击"立即使用"后跳转的路由路径
 */
const props = defineProps({
  icon: {
    type: [Object, Function], // 图标为 Vue 组件对象
    required: true
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  to: {
    type: String,
    required: true
  }
})

/**
 * 点击"立即使用"按钮（或整张卡片）：编程式导航到对应功能页面
 */
const handleUse = () => {
  router.push(props.to)
}
</script>

<template>
  <!-- 卡片主体：白底、圆角、轻微阴影，悬停时上浮 -->
  <div class="feature-card" @click="handleUse">
    <!-- 图标区域：深蓝圆形底 + 金色描边 -->
    <div class="card-icon">
      <el-icon :size="24" color="#ffffff">
        <component :is="icon" />
      </el-icon>
    </div>

    <!-- 模块名称 -->
    <h3 class="card-title">{{ title }}</h3>

    <!-- 功能描述 -->
    <p class="card-desc">{{ description }}</p>

    <!-- 操作按钮：.stop 阻止冒泡，避免与卡片点击重复触发 -->
    <el-button class="card-btn" type="primary" @click.stop="handleUse">
      立即使用
      <el-icon class="btn-arrow"><ArrowRight /></el-icon>
    </el-button>
  </div>
</template>

<style scoped>
/* 卡片容器 */
.feature-card {
  background-color: #ffffff;
  border-radius: 10px;
  padding: 40px 28px 36px;
  text-align: center;
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 16px rgba(26, 58, 92, 0.06);
  cursor: pointer;
  /* 上浮与阴影变化的过渡动画 */
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

/* 悬停效果：卡片轻微上浮，阴影加深 */
.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 28px rgba(26, 58, 92, 0.14);
}

/* 图标圆形外框 */
.card-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  border-radius: 50%;
  background-color: var(--color-primary);
  /* 金色细描边点缀 */
  border: 2px solid var(--color-gold);
  display: flex;
  align-items: center;
  justify-content: center;
  /* 悬停时图标背景轻微变亮 */
  transition: background-color 0.25s ease;
}

.feature-card:hover .card-icon {
  background-color: var(--color-primary-light);
}

/* 模块名称 */
.card-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  margin-bottom: 12px;
}

/* 功能描述 */
.card-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin-bottom: 24px;
}

/* "立即使用"按钮 */
.card-btn {
  font-weight: 500;
  border-radius: 6px;
  padding: 10px 22px;
}

/* 按钮内箭头图标与文字对齐 */
.btn-arrow {
  margin-left: 4px;
}
</style>
