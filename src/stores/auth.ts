import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
    // 存儲使用者是否已登入
    const isAuthenticated = ref(false)
    // 存儲目前使用者名稱
    const user = ref('')

    // 登入方法
    const login = (username: string, pass: string) => {
        // 簡單的模擬驗證邏輯
        // 帳號: admin, 密碼: 1234
        if (username === 'admin' && pass === '1234') {
            isAuthenticated.value = true
            user.value = 'Admin'
            return true
        }
        return false
    }

    // 登出方法
    const logout = () => {
        isAuthenticated.value = false
        user.value = ''
    }

    return { isAuthenticated, user, login, logout }
})
