import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export interface Component {
  id: string
  layoutId: string
  type: 'bin' | 'pillar' | 'marker' | 'machine'
  x: number
  y: number
  width: number
  height: number
  rotation: number
  shapePoints?: { x: number, y: number }[]
  code?: string
  props?: any
  data?: any // For WIP data
}

export interface Layout {
  id: string
  name: string
  width: number
  height: number
  floor?: string
  area?: string
  components?: Component[]
}

export const useWarehouseStore = defineStore('warehouse', () => {
  const layouts = ref<Layout[]>([])
  const currentLayout = ref<Layout | null>(null)
  const binCounts = ref<Record<string, number>>({})

  // Fetch All Layouts
  const fetchLayouts = async () => {
    try {
      const res = await api.get('/layouts/')
      layouts.value = res.data
    } catch (err) {
      console.error('Failed to fetch layouts', err)
    }
  }

  // Fetch Single Layout with Components
  const fetchLayoutDetails = async (id: string) => {
    try {
      const res = await api.get(`/layouts/${id}`)
      currentLayout.value = res.data

      // Auto fetch counts for this layout
      if (res.data.components) {
        const codes = res.data.components
          .filter((c: Component) => c.type === 'bin' && c.code)
          .map((c: Component) => c.code)
        if (codes.length > 0) {
          fetchBinCounts(codes)
        }
      }
    } catch (err) {
      console.error('Failed to fetch layout details', err)
    }
  }

  // Fetch Bin Counts
  const fetchBinCounts = async (binCodes: string[]) => {
    try {
      const res = await api.post('/data/counts', { binCodes })
      binCounts.value = { ...binCounts.value, ...res.data }
    } catch (err) {
      console.error('Failed to fetch bin counts', err)
    }
  }

  // Add Layout
  const addLayout = async (name: string, width = 800, height = 600) => {
    try {
      const res = await api.post('/layouts/', { name, width, height })
      layouts.value.push(res.data)
      return res.data.id
    } catch (err) {
      console.error('Failed to create layout', err)
      return null
    }
  }

  // Remove Layout
  const removeLayout = async (id: string) => {
    try {
      await api.delete(`/layouts/${id}`)
      layouts.value = layouts.value.filter(l => l.id !== id)
      if (currentLayout.value?.id === id) currentLayout.value = null
    } catch (err) {
      console.error('Failed to delete layout', err)
    }
  }

  // Add Component
  const addComponent = async (layoutId: string, component: Partial<Component>) => {
    try {
      const res = await api.post(`/layouts/${layoutId}/components`, component)
      if (currentLayout.value && currentLayout.value.id === layoutId) {
        if (!currentLayout.value.components) currentLayout.value.components = []
        currentLayout.value.components.push(res.data)
      }
    } catch (err) {
      console.error('Failed to add component', err)
    }
  }

  // Update Component
  const updateComponent = async (componentId: string, updates: Partial<Component>) => {
    try {
      const res = await api.put(`/layouts/components/${componentId}`, updates)
      if (currentLayout.value && currentLayout.value.components) {
        const idx = currentLayout.value.components.findIndex(c => c.id === componentId)
        if (idx !== -1) {
          currentLayout.value.components[idx] = res.data
        }
      }
    } catch (err) {
      console.error('Failed to update component', err)
    }
  }

  // Remove Component
  const removeComponent = async (componentId: string) => {
    try {
      await api.delete(`/layouts/components/${componentId}`)
      if (currentLayout.value && currentLayout.value.components) {
        currentLayout.value.components = currentLayout.value.components.filter(c => c.id !== componentId)
      }
    } catch (err) {
      console.error('Failed to delete component', err)
    }
  }

  // Fetch WIP Data
  const fetchWipData = async (binCodes: string[]) => {
    try {
      const res = await api.post('/data/wip', { binCodes })
      return res.data
    } catch (err) {
      console.error('Failed to fetch WIP data', err)
      return {}
    }
  }

  return {
    layouts,
    currentLayout,
    fetchLayouts,
    fetchLayoutDetails,
    addLayout,
    removeLayout,
    addComponent,
    updateComponent,
    removeComponent,
    fetchWipData,
    binCounts
  }
})
