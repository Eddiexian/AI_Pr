<script setup lang="ts">
import { ref, computed } from 'vue'

interface Activity {
  id: number
  title: string
  time: string
  status: 'completed' | 'pending' | 'active'
}

const count = ref(0)
const userName = ref('Guest')
const activities = ref<Activity[]>([
  { id: 1, title: 'System Initialization', time: '10:00 AM', status: 'completed' },
  { id: 2, title: 'Module Loading', time: '10:05 AM', status: 'completed' },
  { id: 3, title: 'AI Neural Sync', time: '10:15 AM', status: 'active' },
  { id: 4, title: 'Data Encryption', time: 'Pending', status: 'pending' },
])

const increment = () => {
  count.value++
}

const statusClass = (status: string) => {
  switch (status) {
    case 'completed': return 'status-completed'
    case 'active': return 'status-active'
    case 'pending': return 'status-pending'
    default: return ''
  }
}

const headerStyle = computed(() => ({
  transform: `translateY(${count.value * 2}px)` // Subtle movement effect
}))
</script>

<template>
  <div class="dashboard-container">
    <div class="glass-panel">
      <header :style="headerStyle" class="header">
        <h1>Welcome, {{ userName }}</h1>
        <p class="subtitle">Vue 3 Composition API • TypeScript • Glassmorphism</p>
      </header>

      <section class="interactive-zone">
        <div class="card counter-card">
          <h2>Interactive Core</h2>
          <div class="counter-display">{{ count }}</div>
          <button @click="increment" class="btn-primary">
            Sync Interaction
          </button>
        </div>

        <div class="card list-card">
          <h2>System Logs</h2>
          <ul>
            <li v-for="item in activities" :key="item.id" class="list-item">
              <span class="item-title">{{ item.title }}</span>
              <span class="item-time">{{ item.time }}</span>
              <span class="status-badge" :class="statusClass(item.status)">
                {{ item.status }}
              </span>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* Scoped styles mainly for layout, but we will put variables in global style.css for consistency */

.dashboard-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: transparent; /* Handled by global body bg */
  color: white;
  font-family: 'Inter', sans-serif;
}

.glass-panel {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 3rem;
  width: 100%;
  max-width: 900px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  transition: all 0.3s ease;
}

.glass-panel:hover {
  box-shadow: 0 12px 40px 0 rgba(0, 100, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.2);
}

.header {
  margin-bottom: 3rem;
  text-align: center;
  transition: transform 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
}

h1 {
  font-size: 3rem;
  margin: 0;
  background: linear-gradient(to right, #6ee7b7, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  letter-spacing: -1px;
}

.subtitle {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.1rem;
  margin-top: 0.5rem;
}

.interactive-zone {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 768px) {
  .interactive-zone {
    grid-template-columns: 1fr 1.5fr;
  }
}

.card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-5px);
  border-color: rgba(59, 130, 246, 0.5);
}

h2 {
  font-size: 1.2rem;
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #e2e8f0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 0.5rem;
}

.counter-display {
  font-size: 4rem;
  font-weight: 700;
  text-align: center;
  margin: 1rem 0;
  color: #60a5fa;
  text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.2s;
  font-size: 1rem;
}

.btn-primary:hover {
  filter: brightness(1.2);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.list-item:last-child {
  border-bottom: none;
}

.item-title {
  font-weight: 500;
}

.item-time {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.status-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.status-completed {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.status-active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
  animation: pulse 2s infinite;
}

.status-pending {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}
</style>
