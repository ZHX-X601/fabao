<!--
  AppHeader.vue —— 顶部导航栏组件
  布局：左侧 Logo + "法宝"品牌名，中间功能导航链接，右侧登录/注册或用户信息
  支持登录注册弹窗，登录后显示用户名与退出按钮
-->
<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuth } from '@/composables/useAuth'

const { user, isLoggedIn, login, register, logout } = useAuth()

// 导航菜单数据
const navLinks = [
  { path: '/ai-consult', label: 'AI法律咨询' },
  { path: '/doc-generate', label: '文书生成' },
  { path: '/contract-review', label: '合同审查' },
  { path: '/about', label: '关于我们' }
]

// ========== 登录/注册弹窗控制 ==========
const loginVisible = ref(false)
const registerVisible = ref(false)

// 登录表单数据
const loginForm = reactive({ username: '', password: '' })
// 注册表单数据
const registerForm = reactive({ username: '', email: '', password: '' })

// 表单提交中状态（防止重复提交）
const submitting = ref(false)

/** 打开登录弹窗 */
function openLogin() {
  loginVisible.value = true
}

/** 打开注册弹窗 */
function openRegister() {
  registerVisible.value = true
}

/** 切换到注册（从登录弹窗跳转） */
function goRegister() {
  loginVisible.value = false
  registerVisible.value = true
}

/** 切换到登录（从注册弹窗跳转） */
function goLogin() {
  registerVisible.value = false
  loginVisible.value = true
}

/** 提交登录 */
async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  submitting.value = true
  try {
    await login({ username: loginForm.username, password: loginForm.password })
    ElMessage.success('登录成功')
    loginVisible.value = false
    loginForm.username = ''
    loginForm.password = ''
  } catch {
    // 错误已在 http.js 拦截器中提示
  } finally {
    submitting.value = false
  }
}

/** 提交注册 */
async function handleRegister() {
  if (!registerForm.username || !registerForm.email || !registerForm.password) {
    ElMessage.warning('请填写完整注册信息')
    return
  }
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  submitting.value = true
  try {
    await register({ ...registerForm })
    ElMessage.success('注册成功，请登录')
    registerVisible.value = false
    // 注册成功后自动打开登录弹窗，并填入用户名
    loginForm.username = registerForm.username
    loginVisible.value = true
    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
  } catch {
    // 错误已在 http.js 拦截器中提示
  } finally {
    submitting.value = false
  }
}

/** 退出登录 */
function handleLogout() {
  logout()
  ElMessage.success('已退出登录')
}
</script>

<template>
  <!-- 顶部导航栏：吸顶固定，白底带轻微阴影 -->
  <header class="app-header">
    <div class="header-inner container">
      <!-- 左侧品牌区：点击 Logo 返回首页 -->
      <router-link to="/" class="brand">
        <!-- Logo 图标：金色天平 -->
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

      <!-- 中间导航链接区 -->
      <nav class="nav-links">
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

      <!-- 右侧用户区：未登录显示登录/注册按钮，已登录显示用户名与退出 -->
      <div class="user-area">
        <template v-if="isLoggedIn">
          <span class="user-name">{{ user.username }}</span>
          <el-button type="text" class="logout-btn" @click="handleLogout">退出</el-button>
        </template>
        <template v-else>
          <el-button type="text" class="auth-btn" @click="openLogin">登录</el-button>
          <el-button type="primary" class="auth-btn register-btn" @click="openRegister">注册</el-button>
        </template>
      </div>
    </div>
  </header>

  <!-- 登录弹窗 -->
  <el-dialog v-model="loginVisible" title="登录法宝" width="400px" align-center>
    <el-form :model="loginForm" label-position="top" @keyup.enter="handleLogin">
      <el-form-item label="用户名">
        <el-input v-model="loginForm.username" placeholder="请输入用户名" clearable />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <span class="switch-text">还没有账号？<a @click="goRegister">立即注册</a></span>
        <el-button type="primary" :loading="submitting" @click="handleLogin">登录</el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 注册弹窗 -->
  <el-dialog v-model="registerVisible" title="注册法宝" width="400px" align-center>
    <el-form :model="registerForm" label-position="top">
      <el-form-item label="用户名">
        <el-input v-model="registerForm.username" placeholder="3-50 个字符" clearable />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="registerForm.email" placeholder="请输入邮箱" clearable />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="registerForm.password" type="password" placeholder="至少 6 位" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <span class="switch-text">已有账号？<a @click="goLogin">去登录</a></span>
        <el-button type="primary" :loading="submitting" @click="handleRegister">注册</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
/* 导航栏：固定在页面顶部 */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--header-height);
  background-color: #ffffff;
  border-bottom: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(26, 58, 92, 0.06);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-logo {
  width: 30px;
  height: 30px;
}

.brand-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 2px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 36px;
}

.nav-link {
  position: relative;
  font-size: 15px;
  color: var(--color-text-main);
  padding: 6px 2px;
  transition: color 0.2s ease;
}

.nav-link:hover {
  color: var(--color-gold);
}

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
  transform: translateX(-50%);
}

/* 用户区 */
.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 14px;
  color: var(--color-primary);
  font-weight: 500;
}

.logout-btn {
  color: var(--color-text-secondary) !important;
  font-size: 14px;
}

.auth-btn {
  font-size: 14px;
}

.register-btn {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

/* 弹窗底部 */
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.switch-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.switch-text a {
  color: var(--color-gold);
  cursor: pointer;
}

/* 响应式 */
@media (max-width: 640px) {
  .nav-links {
    gap: 18px;
  }

  .nav-link {
    font-size: 14px;
  }
}
</style>
