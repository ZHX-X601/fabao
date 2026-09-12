// Vite 构建工具配置文件
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  // 注册 Vue 3 单文件组件支持插件
  plugins: [vue()],
  resolve: {
    alias: {
      // 配置 @ 路径别名，指向 src 目录，方便模块引用
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    // 开发服务器端口
    port: 5173,
    // 启动后自动在浏览器打开
    open: true
  }
})
