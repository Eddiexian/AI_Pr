import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useStorage } from '@vueuse/core'

export interface WIP {
  id: string
  model: string
  grade: string
  op_id: string
}

export interface PPBOX {
  id: string
  box_id: string
  wips: WIP[]
}

export interface Bin {
  id: string
  layoutId: string
  x: number
  y: number
  w: number
  h: number
  code: string
  status: 'empty' | 'occupied' | 'reserved'
  data?: any // Legacy
  contents: PPBOX[] // New semiconductor data
}

export interface Layout {
  id: string
  name: string
  width: number
  height: number
}

export const useWarehouseStore = defineStore('warehouse', () => {
  // Persist to localStorage using VueUse
  const layouts = useStorage<Layout[]>('wms-layouts', [])
  const bins = useStorage<Bin[]>('wms-bins', [])

  const getBinsByLayout = (layoutId: string) => computed(() =>
    bins.value.filter(b => b.layoutId === layoutId)
  )

  const addLayout = (name: string, width = 800, height = 600) => {
    const id = crypto.randomUUID()
    layouts.value.push({ id, name, width, height })
    return id
  }

  const updateLayout = (id: string, updates: Partial<Layout>) => {
    const layout = layouts.value.find(l => l.id === id)
    if (layout) {
      Object.assign(layout, updates)
    }
  }

  const removeLayout = (id: string) => {
    layouts.value = layouts.value.filter(l => l.id !== id)
    bins.value = bins.value.filter(b => b.layoutId !== id)
  }

  const addBin = (layoutId: string, x: number, y: number) => {
    const id = crypto.randomUUID()
    bins.value.push({
      id,
      layoutId,
      x,
      y,
      w: 100,
      h: 100,
      code: `NEW-${bins.value.length + 1}`,
      status: 'empty',
      contents: []
    })
    return id
  }

  const updateBin = (id: string, updates: Partial<Bin>) => {
    const bin = bins.value.find(b => b.id === id)
    if (bin) {
      Object.assign(bin, updates)
    }
  }

  const removeBin = (id: string) => {
    bins.value = bins.value.filter(b => b.id !== id)
  }

  // Helper to mock data for demo
  const mockBinData = (binId: string) => {
    const bin = bins.value.find(b => b.id === binId)
    if (bin && bin.contents.length === 0) {
      bin.contents = [
        {
          id: crypto.randomUUID(),
          box_id: 'PB-2024-001',
          wips: [
            { id: 'W-01', model: 'PNL-X1', grade: 'A', op_id: 'OP-200' },
            { id: 'W-02', model: 'PNL-X1', grade: 'A', op_id: 'OP-200' }
          ]
        },
        {
          id: crypto.randomUUID(),
          box_id: 'PB-2024-002',
          wips: [
            { id: 'W-03', model: 'PNL-Z9', grade: 'B', op_id: 'OP-300' }
          ]
        }
      ]
      bin.status = 'occupied'
    }
  }

  return {
    layouts,
    bins,
    getBinsByLayout,
    addLayout,
    updateLayout,
    removeLayout,
    addBin,
    updateBin,
    removeBin,
    mockBinData
  }
})
