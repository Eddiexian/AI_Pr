import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useStorage } from '@vueuse/core'

// 在製品 (Work In Process) 介面
// 代表生產線上的單個在製品
export interface WIP {
  id: string
  model: string // 型號
  grade: string // 等級
  op_id: string // 操作員 ID
}

// PPBOX 介面
// 代表一個包含多個 WIP 的載具或盒子
export interface PPBOX {
  id: string
  box_id: string // 盒子編號
  wips: WIP[] // 包含的 WIP 列表
}

// 儲存位 (Bin) 介面
// 代表倉庫規劃圖中的一個具體儲位
export interface Bin {
  id: string
  layoutId: string // 所屬佈局 ID
  x: number // X 座標
  y: number // Y 座標
  w: number // 寬度
  h: number // 高度
  code: string // 儲位代碼 (例如: A-01)
  status: 'empty' | 'occupied' | 'reserved' // 狀態: 空閒 | 佔用 | 預留
  data?: any // 舊版資料保留欄位
  contents: PPBOX[] // 儲位內容 (半導體相關資料)
}

// 佈局 (Layout) 介面
// 代表一個倉庫區域的整體佈局圖
export interface Layout {
  id: string
  name: string // 佈局名稱 (例如: 1F A區)
  width: number // 畫布寬度
  height: number // 畫布高度
}

export const useWarehouseStore = defineStore('warehouse', () => {
  // 使用 VueUse 的 useStorage 將資料持久化到 localStorage
  const layouts = useStorage<Layout[]>('wms-layouts', [])
  const bins = useStorage<Bin[]>('wms-bins', [])

  // 根據 Layout ID 取得該佈局下的所有儲位
  const getBinsByLayout = (layoutId: string) => computed(() =>
    bins.value.filter(b => b.layoutId === layoutId)
  )

  // 新增佈局
  const addLayout = (name: string, width = 800, height = 600) => {
    const id = crypto.randomUUID()
    layouts.value.push({ id, name, width, height })
    return id
  }

  // 更新佈局資訊
  const updateLayout = (id: string, updates: Partial<Layout>) => {
    const layout = layouts.value.find(l => l.id === id)
    if (layout) {
      Object.assign(layout, updates)
    }
  }

  // 刪除佈局 (同時刪除該佈局下的所有儲位)
  const removeLayout = (id: string) => {
    layouts.value = layouts.value.filter(l => l.id !== id)
    bins.value = bins.value.filter(b => b.layoutId !== id)
  }

  // 新增儲位
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

  // 更新儲位資訊
  const updateBin = (id: string, updates: Partial<Bin>) => {
    const bin = bins.value.find(b => b.id === id)
    if (bin) {
      Object.assign(bin, updates)
    }
  }

  // 刪除儲位
  const removeBin = (id: string) => {
    bins.value = bins.value.filter(b => b.id !== id)
  }

  // 產生模擬資料 (用於展示)
  // 當儲位內容為空時，填入一些假資料
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
