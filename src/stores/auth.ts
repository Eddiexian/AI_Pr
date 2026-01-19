import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useStorage } from '@vueuse/core'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
    const isAuthenticated = ref(false)
    const user = ref('')
    const role = ref('worker')
    const token = useStorage('auth-token', '') // Persist token

    const login = async (username: string, pass: string) => {
        try {
            const response = await api.post('/auth/login', { username, password: pass })
            const data = response.data

            token.value = data.token
            user.value = data.user.username
            role.value = data.user.role
            isAuthenticated.value = true
            return true
        } catch (error) {
            console.error('Login failed', error)
            return false
        }
    }

    const logout = () => {
        token.value = ''
        isAuthenticated.value = false
        user.value = ''
        role.value = 'worker'
    }

    return { isAuthenticated, user, role, token, login, logout }
})
