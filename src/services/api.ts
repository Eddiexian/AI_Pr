import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
    baseURL: 'http://localhost:5000/api', // Adjust if backend port differs
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request Interceptor to add Token
api.interceptors.request.use(config => {
    const authStore = useAuthStore()
    if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
})

// Response Interceptor for Errors
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            // Handle Unauthorized (Logout)
            const authStore = useAuthStore()
            authStore.logout()
        }
        return Promise.reject(error)
    }
)

export default api
