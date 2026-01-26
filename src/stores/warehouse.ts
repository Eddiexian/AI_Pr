// src/stores/warehouse.ts
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
  shapePoints?: { x: number; y: number }[]
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

  // 原本就有的：用來做顏色用的 mock 數量
  const binCounts = ref<Record<string, number>>({})

  // 新增：每個儲位底下 Cassette 數量（真正從 DB 算出來）
  const binCassetteCounts = ref<Record<string, number>>({})

  // Fetch All Layouts
  const fetchLayouts = async () => {
    try {
      const res = await api.get('/layouts/')
      layouts.value = res.data
    } catch (err) {
      console.error('Failed to fetch layouts', err)
    }
  }

  // Fetch Bin Counts（原本的 mock API）
  const fetchBinCounts = async (binCodes: string[]) => {
    try {
      const res = await api.post('/data/counts', { binCodes })
      binCounts.value = { ...binCounts.value, ...res.data }
    } catch (err) {
      console.error('Failed to fetch bin counts', err)
    }
  }

  // 新增：Fetch Cassette Counts（真正算 Cassette 數量）
  const fetchCassetteCounts = async (binCodes: string[]) => {
    try {
      if (!binCodes.length) return
      const res = await api.post('/data/cassette-counts', { binCodes })
      // 直接覆蓋或 merge 都可以，看你需求
      binCassetteCounts.value = { ...binCassetteCounts.value, ...res.data }
    } catch (err) {
      console.error('Failed to fetch cassette counts', err)
    }
  }

  // Fetch Single Layout with Components
  const fetchLayoutDetails = async (id: string) => {
    try {
      const res = await api.get(`/layouts/${id}`)
      currentLayout.value = res.data

      // Auto fetch counts for this layout（原本的 mock counts）
      if (res.data.components) {
        const codes = res.data.components
          .filter((c: Component) => c.type === 'bin' && c.code)
          .map((c: Component) => c.code as string)

        if (codes.length > 0) {
          // 原本就有的：隨機數，若之後不需要可以拿掉
          fetchBinCounts(codes)

          // 新增：一進 layout 時，也一次抓 Cassette 數量
          fetchCassetteCounts(codes)
        }
      }
    } catch (err) {
      console.error('Failed to fetch layout details', err)
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

  // Update Component（改成就地更新）
  const updateComponent = async (componentId: string, updates: Partial<Component>) => {
    try {
      const res = await api.put(`/components/${componentId}`, updates)
      if (currentLayout.value && currentLayout.value.components) {
        const idx = currentLayout.value.components.findIndex(c => c.id === componentId)
        if (idx !== -1) {
          const comp = currentLayout.value?.components?.[idx]
          if (!comp) return
          Object.assign(comp, res.data)
        }
      }
    } catch (err) {
      console.error('Failed to update component', err)
    }
  }


  const locateByChipOrCassette = async (payload: { chipId?: string; cassetteId?: string }) => {
    try {
      const res = await api.post('/data/locate', payload)
      return res.data   // { bin_code, cassette_id, chip_id } 或 {}
    } catch (err) {
      console.error('Failed to locate by chip/cassette', err)
      return {}
    }
  }

  // Remove Component
  const removeComponent = async (componentId: string) => {
    try {
      await api.delete(`/components/${componentId}`)
      if (currentLayout.value && currentLayout.value.components) {
        currentLayout.value.components =
          currentLayout.value.components.filter(c => c.id !== componentId)
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

  const updateLayout = async (layoutId: string, payload: { width: number, height: number }) => {
    await api.put(`/layouts/${layoutId}`, payload)
    // 注意：currentLayout 是 ref，需要 .value
    if (currentLayout.value && currentLayout.value.id === layoutId) {
      currentLayout.value.width = payload.width
      currentLayout.value.height = payload.height
    }
  }

  return {
    layouts,
    currentLayout,
    binCounts,
    binCassetteCounts,      // <<< 新增 export

    fetchLayouts,
    fetchLayoutDetails,
    fetchBinCounts,
    fetchCassetteCounts,    // <<< 新增 export
    locateByChipOrCassette,
    addLayout,
    removeLayout,
    addComponent,
    updateComponent,
    removeComponent,
    fetchWipData,
    updateLayout,
  }
})
