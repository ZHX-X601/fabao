# Vue 页面动态展示机制讲解（法宝项目为例）

> 本文基于 `D:\Projects\AiProjects\fabao` 项目源码逐行核对编写。回答一个问题：**App.vue 是怎么做到"动态展示其他页面"的**，以及它和你之前了解的手动切换写法有什么区别。

---

## 0. 一句话结论

本项目**没有用**你之前那种「数组 + `activeIndex` + 动态组件」的方式，而是用了 **Vue Router（路由）**：

- 每个页面有一个 URL 路径：`/`、`/ai-consult`、`/doc-generate`、`/contract-review`；
- App.vue 里的 `<router-view>` 就是"动态出口"：**地址栏变了 → 路由匹配 → 出口换组件**；
- 你熟悉的 `<component :is>` 依然在，只是它被包在 `router-view` 的作用域插槽里，外面再套一层 `<transition>` 做淡入淡出。

即：你了解的那个机制没白学，本项目是把它交给了路由系统来驱动。

---

## 1. 项目结构

```
src/
├── main.js                  # 入口：创建应用、注册 router
├── App.vue                  # 根组件：Header + router-view + Footer
├── router/
│   └── index.js             # 路由表：路径 → 页面组件
├── views/                   # 页面组件（被动态展示的对象）
│   ├── HomePage.vue         # 首页（/）
│   ├── AiConsult.vue        # AI法律咨询（/ai-consult）
│   ├── DocGenerate.vue      # 文书生成（/doc-generate）
│   └── ContractReview.vue   # 合同审查（/contract-review）
├── components/              # 公共组件（Header/Footer/FeatureCard）
└── assets/styles/global.css
```

页面布局是"上下固定、中间换"：顶部导航栏 AppHeader、底部信息栏 AppFooter 永远不变，**只有中间 `<router-view>` 在动态换内容**——这就是 SPA 的"布局复用 + 内容动态"。

---

## 2. 页面切换的 6 步链路

一次点击导航到页面换掉，共 6 步，涉及 4 个文件：

| 步骤 | 发生什么 | 在哪个文件 |
|---|---|---|
| 1 | 点击导航或按钮 | AppHeader.vue（router-link）/ HomePage.vue（router.push） |
| 2 | 地址栏 URL 变化（如变成 /ai-consult） | 浏览器 |
| 3 | 路由表匹配：path 找到对应 component | router/index.js |
| 4 | 懒加载：首次访问才下载页面组件 | router/index.js 的 `() => import(...)` |
| 5 | router-view 拿到匹配的组件对象 | App.vue 的 v-slot |
| 6 | transition + `<component :is>` 渲染新页面 | App.vue |

### 第 1 步：触发跳转（两个入口）

**入口 A：声明式导航（AppHeader.vue）**——`router-link` 渲染成 `<a href>`，点击即改 URL：

```vue
<router-link
  v-for="item in navLinks"
  :key="item.path"
  :to="item.path"
  class="nav-link"
  active-class="nav-link--active"
>
  {{ item.label }}
</router-link>
```

其中 `navLinks` 是：

```js
const navLinks = [
  { path: '/ai-consult', label: 'AI法律咨询' },
  { path: '/doc-generate', label: '文书生成' },
  { path: '/contract-review', label: '合同审查' }
]
```

**入口 B：编程式导航（HomePage.vue）**——JS 里调用 `router.push()`，还能带参数：

```js
import { useRouter } from 'vue-router'
const router = useRouter()

// 跳转到咨询页，并把用户输入的问题通过 query 带过去
const handleConsult = () => {
  router.push({
    path: '/ai-consult',
    query: question.value.trim() ? { q: question.value.trim() } : {}
  })
}
```

两种方式殊途同归：最终都是**改变 URL**。

### 第 3~4 步：路由表匹配（router/index.js）

```js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',                name: 'Home',          component: () => import('@/views/HomePage.vue'),       meta: { title: '首页' } },
  { path: '/ai-consult',      name: 'AiConsult',     component: () => import('@/views/AiConsult.vue'),      meta: { title: 'AI法律咨询' } },
  { path: '/doc-generate',    name: 'DocGenerate',   component: () => import('@/views/DocGenerate.vue'),    meta: { title: '文书生成' } },
  { path: '/contract-review', name: 'ContractReview', component: () => import('@/views/ContractReview.vue'), meta: { title: '合同审查' } },
]

const router = createRouter({
  history: createWebHistory(),  // HTML5 History 模式，URL 不带 #
  routes,
  scrollBehavior() { return { top: 0 } }  // 切页后回到顶部
})

// 全局前置守卫：切页时自动改浏览器标签页标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 法宝AI法律助手` : '法宝 - AI法律助手'
  next()
})

export default router
```

这段代码就是"页面地图"：`path` 是地址，`component` 是页面组件，一一对应。

### 第 5~6 步：App.vue 动态渲染（核心）

```vue
<!-- App.vue 模板中唯一"会变"的地方 -->
<router-view v-slot="{ Component }">
  <transition name="fade" mode="out-in">
    <component :is="Component" />
  </transition>
</router-view>
```

逐层拆解：

| 代码 | 作用 |
|---|---|
| `<router-view>` | 路由出口，由 Vue Router 提供，内部自动拿到"当前 URL 匹配的组件" |
| `v-slot="{ Component }"` | 作用域插槽，把匹配到的组件对象解构出来 |
| `<transition mode="out-in">` | 切换动画容器，旧组件完全消失后新组件再进来 |
| `<component :is="Component" />` | 动态组件，`:is` 是哪个组件对象就实例化渲染哪个 |

一句话：**`router-view` 负责"算出现在该显示谁"，`<component :is>` 负责"把它画出来"。**

---

## 3. URL 到底是怎么切换的（底层拆解）

### 3.1 点击导航那一刻：发生了什么

`<router-link to="/ai-consult">` 最终渲染成 `<a href="/ai-consult">`。但点击时的行为**不是浏览器默认跳转**，而是被 Vue Router 接管：

```
点击 <a href="/ai-consult">
  │
  ├─ 浏览器默认行为：整页跳转、重新请求 HTML（已被 e.preventDefault() 阻止）
  │
  └─ Vue Router 接管后的 5 步：
      ① e.preventDefault()             阻止浏览器"刷新式跳转"
      ② 内部调用 router.push('/ai-consult')
      ③ history.pushState(...)         地址栏变成 /ai-consult（不发请求！）
      ④ currentRoute.value = 新路由对象  更新响应式状态
      ⑤ router-view 依赖 currentRoute   重新渲染 → 换组件
```

关键点 1：**`pushState` 只改地址栏、不发网络请求**——这是 SPA"切换页面但浏览器不刷新"的全部秘密，也是你看到切换瞬间完成、无闪烁的原因。

关键点 2：**`pushState` 不会触发任何事件**。既然没人通知，第 ④ 步就是 Vue Router"自己改完自己通知"。

### 3.2 那座看不见的桥：currentRoute 响应式对象

Vue Router 内部（简化示意，非源码）：

```js
class Router {
  // 当前路由：一个 ref 响应式对象 —— router-view 就盯着它
  currentRoute = ref(ROUTE_START)

  // 主动跳转（router-link / router.push 走这里）
  push(to) {
    const target = this.resolve(to)                       // ① 解析目标：path + query + 匹配的路由记录
    history.pushState(target.state, '', target.fullPath)  // ② 改地址栏（不发请求）
    this.currentRoute.value = target                      // ③ 自己更新响应式状态 → 触发依赖方重渲染
  }

  // 浏览器前进/后退（URL 是浏览器改的，事件是浏览器发的）
  listen() {
    window.addEventListener('popstate', () => {
      this.currentRoute.value = this.resolve(location.pathname + location.search)
    })
  }
}
```

而 `<router-view>` 内部（概念示意）：

```js
const currentRoute = inject(routerKey).currentRoute        // 拿到那个响应式对象
const matched = computed(() => currentRoute.value.matched) // 计算属性：依赖它
// currentRoute.value 一变 → matched 重新计算 → 组件换成新的
```

**所以 URL 和页面之间的桥是：**

> URL 变了（无论谁改的）→ `currentRoute.value` 更新 → 依赖它的计算属性失效 → `router-view` 重渲染 → `<component :is>` 实例化新组件。

### 3.3 三条路径，殊途同归

| 路径 | URL 是谁改的 | 有没有事件 | 结果 |
|---|---|---|---|
| 点 router-link / router.push() | Vue Router 用 pushState 主动改 | 无事件，Router 自己更新 currentRoute | 地址栏变 + 组件切换，无刷新 |
| 浏览器前进/后退按钮 | 浏览器改（历史栈回退） | 触发 popstate | Router 监听后更新 currentRoute → 组件切换 |
| 地址栏手输 / F5 刷新 | 浏览器整页加载 | 无（应用全新启动） | 返回 index.html → 应用重启 → 路由读 URL 匹配渲染 |

注意第三条：**刷新不是"SPA 切换"，是整个应用重新启动一遍**。能"恢复"到当前页，是因为启动时路由会读 `location.pathname` 去匹配——URL 是唯一真相源。

### 3.4 那 query 参数（?q=xxx）呢

```js
router.push({ path: '/ai-consult', query: { q: '劳动纠纷' } })
// 地址栏变成：/ai-consult?q=劳动纠纷
```

- `pushState` 写入的是完整路径（path + query），所以参数会一起进地址栏、一起进历史记录；
- 接收方用 `useRoute().query.q` 读取（本项目 AiConsult.vue 预留了这项能力）。

### 3.5 对比：你之前的写法为什么"URL 不变"

你的手动版：`@click="activeIndex = index"` 只改内存里的数字。浏览器对这次变化一无所知——地址栏不动、历史栈没有记录、刷新回到第 0 项。所以它天然无法支持分享、前进后退、刷新恢复。

> URL 驱动的本质：**把浏览器变成页面状态的记录者**。

---

## 4. 两种写法对比

| 维度 | 你的写法（状态驱动） | 本项目（URL 驱动） |
|---|---|---|
| 切换的"开关" | 内存里的 activeIndex 数字 | 地址栏里的 URL 字符串 |
| 页面有没有身份 | 没有，只有"第几个" | 每个页面一个独立 URL，可收藏、可分享 |
| 浏览器前进/后退 | 不支持 | 原生支持，历史记录里每一步都是页面 |
| 刷新页面 | 回到主页 | 停留在当前 URL 对应的页面 |
| 组件加载 | 启动时全部 import，打包成一个文件 | 路由懒加载，用到哪个才下载哪个 |
| 选中高亮 | 手动比较 index === activeIndex | router-link 自动加 active 类 |
| 页面标题 | 不涉及 | 路由 meta.title + 全局守卫自动设置 |
| 页面状态 | 切走即销毁 | 同样销毁（可用 keep-alive 缓存） |
| 适用场景 | 组件工具面板、无需 URL 的内嵌切换 | 多页面应用：需要分享、收藏、SEO、历史记录 |

---

## 5. 动手练习

### 练习 1：给本项目新增"法律法规检索"页面

只需改 3 处，App.vue 一行都不用动：

1. 新建 `src/views/Laws.vue`（随便写点内容）；
2. `router/index.js` 的 routes 数组加一行：
   ```js
   { path: '/laws', name: 'Laws', component: () => import('@/views/Laws.vue'), meta: { title: '法规检索' } },
   ```
3. `AppHeader.vue` 的 navLinks 加一项：
   ```js
   { path: '/laws', label: '法规检索' }
   ```

完成。懒加载、激活高亮、页面标题全部自动生效——这就是路由方案的"扩展成本低"。

### 练习 2：把你之前的手动版改造成路由版

| 原写法 | 改造成路由写法 |
|---|---|
| 静态 import 全部页面 | 路由表里写 `() => import(...)` 懒加载 |
| menus 数组 | routes 数组：{ path, name, component } |
| `@click="activeIndex = index"` | `<router-link :to="path">` 或 `router.push(path)` |
| 手动比较 index === activeIndex 高亮 | active-class 属性，框架自动高亮 |
| `<component :is="menus[activeIndex].component" />` | `<router-view />`（可加 transition） |

### 练习 3：给切换加缓存

切走再切回时想保留页面输入：

```vue
<router-view v-slot="{ Component }">
  <keep-alive>
    <component :is="Component" />
  </keep-alive>
</router-view>
```

（本项目没有用 keep-alive，切走即销毁组件。）

---

## 6. FAQ

**Q1：router-view 和 component :is 是什么关系？**
`<component :is="X">` 是"给我组件对象 X，我就渲染它"；`router-view` 是"我根据 URL 算出该渲染谁"。两者是上下游：router-view 算，component :is 画。

**Q2：点击导航页面换了，但浏览器没刷新，为什么？**
SPA 特性。router-link 拦截了 `<a>` 的默认跳转，只改 URL 并触发路由更新，页面 DOM 不重新加载，Header/Footer 也不重绘。

**Q3：刷新后为什么还能停在当前页？**
因为页面状态没有存在内存里，而是存在 URL 里。刷新 = 重新加载应用 → 路由读 URL → 匹配渲染。URL 是唯一真相源。

**Q4：为什么组件用 () => import() 而不是直接 import？**
直接 import 全部页面会合成一个巨大的首屏 JS；懒加载把每个页面拆成独立 chunk，首屏只下载当前页代码。

**Q5：生产部署后刷新子页面 404 怎么办？**
History 模式要求服务器把不存在的路径回退到 index.html（Nginx 配 `try_files $uri $uri/ /index.html;`）。不想配服务器就改用 createWebHashHistory（URL 带 #）。

---

## 7. 学习建议

1. `npm run dev` 跑起来，点导航看地址栏变化、浏览器前进后退、页面标题；
2. DevTools → Network 里切页面，观察每个页面 chunk 是不是首次访问才下载（验证懒加载）；
3. 做练习 1 和练习 2，各 10 分钟；
4. 再深入：beforeEach 守卫做登录鉴权、route.params 动态路径、keep-alive 缓存、嵌套路由（children）。

---

*本文档基于项目源码（App.vue / main.js / router/index.js / AppHeader.vue / HomePage.vue / FeatureCard.vue / vite.config.js / package.json）逐行核对编写。*
