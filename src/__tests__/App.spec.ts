import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../App.vue'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', component: { template: '<div>Dashboard</div>' } }
    ]
})

describe('App.vue', () => {
    it('renders the navigation brand text', async () => {
        const wrapper = mount(App, {
            global: {
                plugins: [router]
            }
        })

        expect(wrapper.text()).toContain('WMS 2D Layout System')
    })
})
