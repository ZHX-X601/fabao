<!--
  AppHeader.vue —— 顶部导航栏组件
  布局：左侧 Logo + "法宝"品牌名，右侧三个功能模块导航链接
  使用 router-link 实现单页面无刷新跳转，激活链接以金色高亮
-->
<script setup>
/**
 * 导航菜单数据
 * path：跳转路径（与 router/index.js 中的路由配置对应）
 * label：菜单显示文字
 */
const navLinks = [
  { path: '/ai-consult', label: 'AI法律咨询' },
  { path: '/doc-generate', label: '文书生成' },
  { path: '/contract-review', label: '合同审查' },
  { path: '/about', label: '关于我们' }
]
</script>

<template>
  <!-- 顶部导航栏：吸顶固定，白底带轻微阴影 -->
  <header class="app-header">
    <div class="header-inner container">
      <!-- 左侧品牌区：点击 Logo 返回首页 -->
      <router-link to="/" class="brand">
        <!-- Logo 图标：金色天平（使用内联 SVG，无需额外依赖） -->
        <svg class="brand-logo" viewBox="0 0 32 32" aria-hidden="true">
          <rect width="32" height="32" rx="6" fill="#1a3a5c" />
          <path
            d="M16 7v18M10 10h12M11 10l-3 7h6l-3-7zm10 0l-3 7h6l-3-7zM12 25h8"
            fill="none"
            stroke="#c9a96e"
            stroke-width="1.6"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span class="brand-name">法宝</span>
      </router-link>

      <!-- 右侧导航链接区 -->
      <nav class="nav-links">
        <!-- 遍历导航数据生成 router-link；router-link-active 为当前路由激活时自动添加的类名 -->
        <router-link
          v-for="item in navLinks"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          active-class="nav-link--active"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </div>
  </header>
</template>

<style scoped>
/* 导航栏：固定在页面顶部 */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100; /* 保证导航栏始终覆盖在其他内容之上 */
  height: var(--header-height);
  background-color: #ffffff;
  border-bottom: 1px solid var(--color-border);
  /* 轻微底部阴影，增强层次感 */
  box-shadow: 0 2px 8px rgba(26, 58, 92, 0.06);
}

/* 导航栏内容区：左右两端对齐 */
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

/* 品牌区样式 */
.brand {
  display: flex;
  align-items: center;
  gap: 8px; /* Logo 与文字的间距 */
}

.brand-logo {
  width: 30px;
  height: 30px;
}

.brand-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 2px; /* 字距拉开，显得庄重 */
}

/* 导航链接容器 */
.nav-links {
  display: flex;
  align-items: center;
  gap: 36px; /* 各导航项之间的间距 */
}

/* 单个导航链接 */
.nav-link {
  position: relative;
  font-size: 15px;
  color: var(--color-text-main);
  padding: 6px 2px;
  transition: color 0.2s ease; /* 颜色过渡动画 */
}

/* 悬停时文字变为金色 */
.nav-link:hover {
  color: var(--color-gold);
}

/* 当前路由激活状态：金色文字 + 底部金色短横线 */
.nav-link--active {
  color: var(--color-gold);
  font-weight: 600;
}

.nav-link--active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -4px;
  width: 20px;
  height: 2px;
  background-color: var(--color-gold);
  border-radius: 1px;
  transform: translateX(-50%); /* 水平居中 */
}

/* 响应式：窄屏下缩小导航间距，避免换行拥挤 */
@media (max-width: 640px) {
  .nav-links {
    gap: 18px;
  }

  .nav-link {
    font-size: 14px;
  }
}
</style>
