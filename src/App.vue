<script setup lang="ts">
// Main layout shell
</script>

<template>
  <div class="app-shell">
    <nav class="main-nav">
      <router-link to="/" class="nav-brand">WMS 2D Layout System</router-link>
      <div class="nav-links">
        <router-link to="/">Dashboard</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-nav {
  height: 60px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  padding: 0 2rem;
  justify-content: space-between;
}

.nav-brand {
  font-weight: 700;
  font-size: 1.25rem;
  color: #60a5fa;
  text-decoration: none;
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
  flex: 1;
  position: relative;
}
</style>
