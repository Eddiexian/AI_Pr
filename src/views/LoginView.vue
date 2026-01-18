<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('admin')
const password = ref('1234')
const error = ref('')

const handleLogin = () => {
  if (auth.login(username.value, password.value)) {
    router.push('/')
  } else {
    error.value = '帳號或密碼錯誤 (預設: admin / 1234)'
  }
}
</script>

<template>
  <div class="login-container">
    <div class="glass-panel login-card">
      <h1>無塵室儲位管理系統</h1>
      <p class="subtitle">Semiconductor WMS</p>
      
      <div class="form-group">
        <label>帳號</label>
        <input v-model="username" type="text" placeholder="Username" @keyup.enter="handleLogin" />
      </div>

      <div class="form-group">
        <label>密碼</label>
        <input v-model="password" type="password" placeholder="Password" @keyup.enter="handleLogin" />
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <button @click="handleLogin" class="btn-primary">登入系統</button>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 50% 50%, rgba(30, 41, 59, 1) 0%, rgba(15, 23, 42, 1) 100%);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 3rem;
  text-align: center;
}

h1 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: #fff;
}

.subtitle {
  color: #94a3b8;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
  text-align: left;
}

label {
  display: block;
  color: #cbd5e1;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

input {
  width: 100%;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: white;
  font-size: 1rem;
}

input:focus {
  outline: none;
  border-color: #3b82f6;
  background: rgba(255, 255, 255, 0.1);
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  margin-top: 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

.error-msg {
  color: #f87171;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

/* Reusing glass panel style */
.glass-panel {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
}
</style>
