<script setup lang="ts">
import { useUiStore } from './stores/ui'
import ToastContainer from './components/ToastContainer.vue'

const ui = useUiStore()

function enterFullscreen() {
  const el = document.documentElement;
  if (el.requestFullscreen) {
    el.requestFullscreen();
  } else if ((el as any).webkitRequestFullscreen) {
    (el as any).webkitRequestFullscreen();
  }
}

</script>

<template>
  <div class="app-shell">
    <!-- transition 讓 nav 有滑上消失的動畫 -->
    <transition name="slide-down">
      <nav v-if="ui.showNav" class="main-nav">
        <div class="nav-left">
          <router-link to="/" class="nav-brand">WMS 2D Layout System</router-link>
          <!-- 收起按鈕 -->
          <button class="hide-btn" @click="ui.toggleNav">▲</button>
           <button @click="enterFullscreen">📺 全螢幕</button>
        </div>
        <div class="nav-links">
          <router-link to="/">Dashboard</router-link>
        </div>
      </nav>
    </transition>

    <main class="main-content">
      <router-view></router-view>
      <ToastContainer />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
    height: 100vh; /* 改成height而非min-height */
  display: flex;
  flex-direction: column;
}

.main-nav {
  height: 60px;
  background: rgba(15, 23, 42, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  padding: 0 2rem;
  justify-content: space-between;
}

.nav-left {
  display: flex;
  align-items: center;
}

.nav-brand {
  font-weight: 700;
  font-size: 1.25rem;
  color: #60a5fa;
  text-decoration: none;
}

.hide-btn {
  margin-left: 1rem;
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
}
.hide-btn:hover {
  color: #f8fafc;
}

.nav-links a {
  color: #94a3b8;
  text-decoration: none;
  margin-left: 1.5rem;
  transition: color 0.2s;
}

.nav-links a:hover, .nav-links a.router-link-active {
  color: #f8fafc;
}

.main-content {
  flex: 1; /* 占滿剩餘空間 */
  display: flex;
  flex-direction: column; /* 根據內容需求調整，也可留空 */
  overflow: auto;
}
.app-shell:not(.has-nav) .main-content {
  min-height: 100vh; /* nav 消失時 */
}

/* ▼ Nav 往上隱藏的動畫 ▼ */
.slide-down-leave-active {
  transition: height 0.3s ease, opacity 0.3s ease;
}

.slide-down-leave-from {
  height: 60px;
  opacity: 1;
}

.slide-down-leave-to {
  height: 0;
  opacity: 0;
}
</style>
