/**
 * 路由配置文件
 * 使用 Vue Router 4 的 createWebHistory 模式（HTML5 History 模式）
 */
import { createRouter, createWebHistory } from 'vue-router'

// 路由表：path 为访问路径，name 为路由名称，component 为对应渲染的页面组件
const routes = [
  {
    path: '/', // 首页路径
    name: 'Home',
    component: () => import('@/views/HomePage.vue'), // 路由懒加载，按需打包
    meta: { title: '首页' }
  },
  {
    path: '/ai-consult', // AI 法律咨询页面路径
    name: 'AiConsult',
    component: () => import('@/views/AiConsult.vue'),
    meta: { title: 'AI法律咨询' }
  },
  {
    path: '/doc-generate', // 文书生成页面路径
    name: 'DocGenerate',
    component: () => import('@/views/DocGenerate.vue'),
    meta: { title: '文书生成' }
  },
  {
    path: '/contract-review', // 合同审查页面路径
    name: 'ContractReview',
    component: () => import('@/views/ContractReview.vue'),
    meta: { title: '合同审查' }
  }
]

// 创建路由实例
const router = createRouter({
  // 使用 History 模式，URL 中不会出现 # 号
  history: createWebHistory(),
  routes,
  // 切换路由后自动回到页面顶部
  scrollBehavior() {
    return { top: 0 }
  }
})

// 全局前置守卫：根据路由元信息动态设置浏览器标签页标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 法宝AI法律助手` : '法宝 - AI法律助手'
  next()
})

export default router
