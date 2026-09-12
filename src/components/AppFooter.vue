<!--
  AppFooter.vue —— 底部信息栏组件
  内容：免责声明文字 + 金色分隔线 + 版权信息
  深蓝背景与顶部 Hero 区域呼应，体现法律网站的专业沉稳
-->
<script setup>
// 当前年份，用于版权信息（按实际年份自动更新）
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer">
    <div class="footer-inner container">
      <!-- 免责声明：提示 AI 生成内容仅供参考，不构成正式法律意见 -->
      <p class="disclaimer">
        免责声明：本平台由 AI 智能生成的法律内容仅供参考与学习，不构成正式法律意见。
        如遇实际法律问题，请咨询持有执业资格的专业律师。
      </p>

      <!-- 金色短分隔线 -->
      <div class="divider"></div>

      <!-- 版权信息 -->
      <p class="copyright">© {{ currentYear }} 法宝 - AI法律助手 版权所有</p>
    </div>
  </footer>
</template>

<style scoped>
/* 页脚：深蓝背景 */
.app-footer {
  background-color: var(--color-primary-dark);
  padding: 32px 0 26px;
}

/* 页脚内容居中排列 */
.footer-inner {
  text-align: center;
}

/* 免责声明文字：小号、浅灰蓝色、较大行高保证可读性 */
.disclaimer {
  font-size: 12px;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.55);
  max-width: 760px; /* 限制行宽，避免宽屏下文字过长 */
  margin: 0 auto;
}

/* 金色分隔短线 */
.divider {
  width: 40px;
  height: 2px;
  background-color: var(--color-gold);
  border-radius: 1px;
  margin: 16px auto;
}

/* 版权文字 */
.copyright {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}
</style>
