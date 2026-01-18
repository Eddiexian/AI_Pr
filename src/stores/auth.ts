import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
    const isAuthenticated = ref(false)
    const user = ref('')

    const login = (username: string, pass: string) => {
        // Simple mock auth
        if (username === 'admin' && pass === '1234') {
            isAuthenticated.value = true
            user.value = 'Admin'
            return true
        }
        return false
    }

    const logout = () => {
        isAuthenticated.value = false
        user.value = ''
    }

    return { isAuthenticated, user, login, logout }
})
