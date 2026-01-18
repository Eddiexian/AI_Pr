import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
// We will define these components shortly
import DashboardView from '../views/DashboardView.vue'
import EditorView from '../views/EditorView.vue'
import OperationView from '../views/OperationView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: LoginView
        },
        {
            path: '/',
            name: 'dashboard',
            component: DashboardView,
            meta: { requiresAuth: true }
        },
        {
            path: '/editor/:id',
            name: 'editor',
            component: EditorView,
            meta: { requiresAuth: true }
        },
        {
            path: '/operation/:id',
            name: 'operation',
            component: OperationView,
            meta: { requiresAuth: true }
        }
    ]
})

router.beforeEach((to, from, next) => {
    const auth = useAuthStore()
    if (to.meta.requiresAuth && !auth.isAuthenticated) {
        next('/login')
    } else {
        next()
    }
})

export default router
