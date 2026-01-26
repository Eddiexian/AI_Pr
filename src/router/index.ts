import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
// 這裡將導入我們即將定義的組件
import DashboardView from '../views/DashboardView.vue'
import EditorView from '../views/EditorView.vue'
import OperationView from '../views/OperationView.vue'
import LoginView from '../views/LoginView.vue'
import AdminView from '../views/AdminView.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: LoginView // 登入頁面
        },
        {
            path: '/',
            name: 'dashboard',
            component: DashboardView,
            meta: { requiresAuth: true } // 需要驗證權限
        },
        {
            path: '/editor/:id',
            name: 'editor',
            component: EditorView,
            meta: { requiresAuth: true ,role: 'admin'} // 需要驗證權限
        },
        {
            path: '/operation/:id',
            name: 'operation',
            component: OperationView,
            meta: { requiresAuth: false } // 需要驗證權限
        },
        {
            path: '/admin',
            name: 'admin',
            component: AdminView, // Use the imported component
            meta: { requiresAuth: true, role: 'admin' }
        }
    ]
})

// 全局前置守衛
// 用於檢查即將訪問的路由是否需要權限驗證
let isAuthChecked = false

router.beforeEach(async (to, _from, next) => {
    const auth = useAuthStore()

    if (!isAuthChecked) {
        await auth.init()
        isAuthChecked = true
    }

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
        return next('/login')
    }

    if (to.meta.role && auth.role !== to.meta.role) {
        alert('權限不足 (Insufficient Permissions)')
        return next('/')
    }

    next()
})
export default router
