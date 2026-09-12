<!--
  App.vue：应用根组件
  页面整体布局：顶部导航栏（AppHeader） + 路由视图（router-view） + 底部信息栏（AppFooter）
-->
<script setup>
// 启用 Composition API 的 <script setup> 语法
// 引入顶部导航栏公共组件
import AppHeader from '@/components/AppHeader.vue'
// 引入底部信息栏公共组件
import AppFooter from '@/components/AppFooter.vue'
</script>

<template>
  <!-- 最外层容器：纵向弹性布局，保证页脚始终贴在页面底部 -->
  <div class="app-wrapper">
    <!-- 顶部导航栏 -->
    <AppHeader />

    <!-- 路由出口：根据当前 URL 渲染匹配到的页面组件 -->
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <!-- 使用过渡动画实现页面切换时的淡入效果 -->
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 底部信息栏 -->
    <AppFooter />
  </div>
</template>

<style scoped>
/* 根容器占满整个视口高度，采用纵向弹性布局 */
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 主内容区占据剩余空间，将页脚挤压到页面底部 */
.app-main {
  flex: 1;
}

/* 路由切换淡入淡出过渡效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
