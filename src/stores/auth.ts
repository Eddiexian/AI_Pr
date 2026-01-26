import { defineStore } from 'pinia'
import { useStorage } from '@vueuse/core'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
    const isAuthenticated = useStorage('auth-isAuthenticated', false)
    const user = useStorage('auth-user', '')
    const role = useStorage('auth-role', 'worker')
    const token = useStorage('auth-token', '')

    const login = async (username: string, pass: string) => {
        try {
            const res = await api.post('/auth/login', { username, password: pass })
            const data = res.data
            token.value = data.token
            user.value = data.user.username
            role.value = data.user.role
            isAuthenticated.value = true
            return true
        } catch (e) {
            return false
        }
    }

    const logout = () => {
        token.value = ''
        isAuthenticated.value = false
        user.value = ''
        role.value = 'worker'
    }

    const init = async () => {
        if (token.value) {
            try {
                const res = await api.get('/auth/verify')
                user.value = res.data.user.username
                role.value = res.data.user.role
                isAuthenticated.value = true
            } catch (e) {
                logout()
            }
        } else {
            logout()
        }
    }

    return { isAuthenticated, user, role, token, login, logout, init }
})
