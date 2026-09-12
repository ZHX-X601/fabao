/**
 * 应用入口文件
 * 职责：创建 Vue 应用实例，并注册路由、Element Plus 组件库等全局插件
 */
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 引入 Element Plus 组件库及其样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 引入 Element Plus 中文语言包（日期选择、分页等组件默认显示中文）
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 引入全局样式（放在组件库样式之后，便于覆盖其默认主题）
import './assets/styles/global.css'

// 创建 Vue 应用实例
const app = createApp(App)

// 注册 Vue Router 路由插件
app.use(router)
// 注册 Element Plus，并指定中文语言
app.use(ElementPlus, { locale: zhCn })

// 将应用挂载到 index.html 中 id 为 app 的节点上
app.mount('#app')
