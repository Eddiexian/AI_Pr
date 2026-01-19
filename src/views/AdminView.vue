<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const users = ref<any[]>([])
const loading = ref(false)

// 獲取使用者列表 (Fetch User List)
const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await api.get('/auth/users')
    users.value = res.data
  } catch (err) {
    console.error('Failed to fetch users', err)
  } finally {
    loading.value = false
  }
}

// 更新使用者角色 (Update User Role)
const updateRole = async (userId: number, role: string) => {
  try {
    await api.put(`/auth/users/${userId}/role`, { role })
    await fetchUsers()
    alert('身分組已更新')
  } catch (err) {
    alert('更新失敗')
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="admin-container">
    <header class="admin-header">
      <h1>使用者管理 (User Management)</h1>
      <button @click="$router.push('/')" class="btn-back">返回儀表板</button>
    </header>

    <div v-if="loading" class="loading">載入中...</div>
    
    <table v-else class="user-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>帳號 (Username)</th>
          <th>現有角色 (Role)</th>
          <th>變更權限 (Change Role)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>
            <span :class="['role-badge', user.role]">{{ user.role }}</span>
          </td>
          <td>
            <div class="role-actions">
              <button @click="updateRole(user.id, 'worker')" :disabled="user.role === 'worker'">Worker</button>
              <button @click="updateRole(user.id, 'maintainer')" :disabled="user.role === 'maintainer'">Maintainer</button>
              <button @click="updateRole(user.id, 'admin')" :disabled="user.role === 'admin'">Admin</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.admin-container {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}
.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}
.user-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  overflow: hidden;
}
.user-table th {
  background: #1e293b;
  padding: 1rem;
  text-align: left;
  border-bottom: 2px solid #334155;
}
.user-table td {
  padding: 1rem;
  border-bottom: 1px solid #334155;
}
.role-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  text-transform: uppercase;
}
.role-badge.admin { background: #ef4444; color: white; }
.role-badge.maintainer { background: #3b82f6; color: white; }
.role-badge.worker { background: #10b981; color: white; }

.role-actions {
  display: flex;
  gap: 0.5rem;
}
.role-actions button {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  border: 1px solid #475569;
  background: transparent;
  color: white;
  cursor: pointer;
}
.role-actions button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.role-actions button:hover:not(:disabled) {
  background: rgba(255,255,255,0.1);
}
.btn-back {
  background: #475569;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
</style>
