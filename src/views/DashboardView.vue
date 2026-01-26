<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWarehouseStore } from '../stores/warehouse'
import { useAuthStore } from '../stores/auth'




const store = useWarehouseStore()
const auth = useAuthStore()
const router = useRouter()
const newLayoutName = ref('')

onMounted(async () => {
    await store.fetchLayouts()
})

const handleCreate = async () => {
  if (!newLayoutName.value) return
  const id = await store.addLayout(newLayoutName.value)
  if (id) {
    newLayoutName.value = ''
    router.push(`/editor/${id}`)
  }
}

const navigateTo = (path: string) => {
  router.push(path)
}


</script>

<template>
  <div class="dashboard">
    <header class="page-header">
      <div>
         <h1>儲位佈局管理 (Warehouse Layouts)</h1>
      </div>
      <div class="user-info">
        <span class="username">{{ auth.user }}</span>
        <span class="role-tag">{{ auth.role }}</span>
        <router-link v-if="auth.role === 'admin'" to="/admin" class="admin-link">管理用戶</router-link>
        <button @click="auth.logout" class="btn-logout">登出</button>
      </div>
    </header>

    <div v-if="auth.role !== 'worker'" class="create-section">
        <h3>新增佈局</h3>
        <div class="create-control">
            <input v-model="newLayoutName" placeholder="請輸入佈局名稱 (New Layout Name)" @keyup.enter="handleCreate" />
            <button @click="handleCreate" class="btn-primary">建立佈局</button>
        </div>
    </div>

    <div class="layout-grid">
      <div v-if="store.layouts.length === 0" class="empty-state">
        <p>目前沒有任何佈局資料，請先在上方建立。</p>
      </div>

      <div v-for="layout in store.layouts" :key="layout.id" class="layout-card">
        <h3>{{ layout.name }}</h3>
        <p class="meta">{{ layout.width }} x {{ layout.height }} px</p>
        <div class="actions">
          <button v-if="auth.role !== 'worker'" @click="navigateTo(`/editor/${layout.id}`)" class="btn-secondary">編輯佈局</button>
          <button @click="navigateTo(`/operation/${layout.id}`)" class="btn-accent">作業模式</button>
          <button v-if="auth.role === 'admin'" @click="store.removeLayout(layout.id)" class="btn-danger">刪除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 1rem;
}

.welcome-text {
  color: #94a3b8;
  margin: 0;
}

.create-section {
    background: rgba(30, 41, 59, 0.5);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 2rem;
}

.create-section h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    font-size: 1.1rem;
}

.create-control {
  display: flex;
  gap: 1rem;
}

input {
  flex: 1;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.75rem 1rem;
  border-radius: 6px;
  color: white;
  min-width: 250px;
}

.layout-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
}

.layout-card {
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.5rem;
  transition: transform 0.2s;
}

.layout-card:hover {
  transform: translateY(-2px);
  border-color: rgba(96, 165, 250, 0.5);
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

button {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  transition: opacity 0.2s;
}

button:hover {
  opacity: 0.9;
}

.btn-primary { background: #3b82f6; color: white; }
.btn-secondary { background: #475569; color: white; }
.btn-accent { background: #10b981; color: white; }
.btn-danger { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.btn-text { background: transparent; color: #94a3b8; }
.btn-text:hover { color: white; }

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 4rem;
  background: rgba(255,255,255,0.02);
  border-radius: 12px;
  border: 2px dashed rgba(255,255,255,0.1);
  color: #94a3b8;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.role-tag {
  background: #334155;
  color: #94a3b8;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  text-transform: uppercase;
}
.admin-link {
  color: #fbbf24;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
}
.admin-link:hover {
  text-decoration: underline;
}
.btn-logout {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 0.4rem 0.8rem;
  border: 1px solid rgba(239, 68, 68, 0.2);
}
</style>
