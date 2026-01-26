<script setup lang="ts">
import { computed, ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useWarehouseStore, type Component } from '../stores/warehouse'

const route = useRoute()
const store = useWarehouseStore()
const layoutId = route.params.id as string

// ==== 縮放狀態 ====
const resizingId = ref<string | null>(null)
const resizeDir = ref<'nw' | 'ne' | 'sw' | 'se' | null>(null)
const startSize = ref({ x: 0, y: 0, width: 0, height: 0 })

const layoutPaddingLeft = 50  // 元件邏輯座標的安全 margin
const layoutPaddingTop = 50   // 如需要也可以給上方一點 margin

const layout = computed(() => store.currentLayout)
const components = computed(() => layout.value?.components || [])
const svgRef = ref<SVGSVGElement | null>(null)

/* ==== Pan & Zoom ==== */
const zoomLevel = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })
const minZoom = ref(1) // 最遠視角（fit layout 時的 zoom）

const startPan = (e: MouseEvent) => {
  if (e.button === 1 || e.button === 2) {
    isPanning.value = true
    panStart.value = { x: e.clientX, y: e.clientY }
    e.preventDefault()
  }
}
const onPanMove = (e: MouseEvent) => {
  if (isPanning.value) {
    const dx = (e.clientX - panStart.value.x) / zoomLevel.value
    const dy = (e.clientY - panStart.value.y) / zoomLevel.value
    offsetX.value -= dx
    offsetY.value -= dy
    clampOffset()
    panStart.value = { x: e.clientX, y: e.clientY }
  }
}
const endPan = () => { isPanning.value = false }

// 可以放大，也可以縮回到最遠視角( minZoom )，但不能更遠
const onWheelZoom = (e: WheelEvent) => {
  e.preventDefault()
  const zoomSpeed = 0.1
  const mouse = getSvgPoint(e)
  const prevZoom = zoomLevel.value

  if (e.deltaY < 0) {
    // 滾輪向上/向前：放大
    zoomLevel.value = Math.min(zoomLevel.value + zoomSpeed, 5)
  } else {
    // 滾輪向下/向後：縮小，但不能比 minZoom 更小
    zoomLevel.value = Math.max(zoomLevel.value - zoomSpeed, minZoom.value)
  }

  if (zoomLevel.value < minZoom.value) {
    zoomLevel.value = minZoom.value
  }

  // 以滑鼠位置為中心縮放
  offsetX.value = mouse.x - (mouse.x - offsetX.value) * (prevZoom / zoomLevel.value)
  offsetY.value = mouse.y - (mouse.y - offsetY.value) * (prevZoom / zoomLevel.value)

  clampOffset()
}

/* ==== Layout Size ==== */
const layoutWidth = ref(0)
const layoutHeight = ref(0)

// 記錄上一次 layout 寬高，用於「以中心為基準」調整元件座標
const prevLayoutWidth = ref(0)
const prevLayoutHeight = ref(0)

watch(layout, l => {
  if (l) {
    layoutWidth.value = l.width
    layoutHeight.value = l.height
    prevLayoutWidth.value = l.width
    prevLayoutHeight.value = l.height
  }
}, { immediate: true })

let layoutSizeTimer: number | undefined
const scheduleSaveLayoutSize = () => {
  if (layout.value) {
    layout.value.width = layoutWidth.value
    layout.value.height = layoutHeight.value
  }
  if (layoutSizeTimer) clearTimeout(layoutSizeTimer)
  layoutSizeTimer = window.setTimeout(() => {
    if (layout.value) {
      store.updateLayout(layout.value.id, {
        width: layoutWidth.value,
        height: layoutHeight.value
      })
    }
  }, 300)
}

/**
 * 以 layout 中心為基準調整元件位置（寬度變更）
 * 例如：原本寬 1000 -> 1400，中心從 500 移到 700，dx=+200，
 * 所有元件 x 一起 +200，看起來是以中心往左右擴增。
 */
watch(layoutWidth, (newW, oldW) => {
  if (!layout.value) return
  if (!oldW) oldW = prevLayoutWidth.value || newW

  const oldCenterX = oldW / 2
  const newCenterX = newW / 2
  const dx = newCenterX - oldCenterX

  for (const comp of components.value) {
    comp.x += dx
  }

  prevLayoutWidth.value = newW
  scheduleSaveLayoutSize()
})

/**
 * 以 layout 中心為基準調整元件位置（高度變更）
 */
watch(layoutHeight, (newH, oldH) => {
  if (!layout.value) return
  if (!oldH) oldH = prevLayoutHeight.value || newH

  const oldCenterY = oldH / 2
  const newCenterY = newH / 2
  const dy = newCenterY - oldCenterY

  for (const comp of components.value) {
    comp.y += dy
  }

  prevLayoutHeight.value = newH
  scheduleSaveLayoutSize()
})

const clampOffset = () => {
  const vw = Math.min(layoutWidth.value, layoutWidth.value / zoomLevel.value)
  const vh = Math.min(layoutHeight.value, layoutHeight.value / zoomLevel.value)
  offsetX.value = Math.max(0, Math.min(layoutWidth.value - vw, offsetX.value))
  offsetY.value = Math.max(0, Math.min(layoutHeight.value - vh, offsetY.value))
}

/* ==== fit 整個 Layout 視角 ==== */
const fitToLayout = () => {
  const container = document.querySelector('.canvas-area') as HTMLElement | null
  if (!container || !layout.value) return

  const layoutW = layout.value.width
  const layoutH = layout.value.height

  const rect = container.getBoundingClientRect()
  const viewW = rect.width
  const viewH = rect.height

  if (viewW === 0 || viewH === 0) return

  const zoomByWidth = layoutW / viewW
  const zoomByHeight = layoutH / viewH
  const fitZoom = Math.max(zoomByWidth, zoomByHeight)

  zoomLevel.value = fitZoom
  minZoom.value = fitZoom

  offsetX.value = 0
  offsetY.value = 0
  clampOffset()
}

/* ==== 拖曳、多選、吸附 ==== */
const getSvgPoint = (e: MouseEvent | WheelEvent) => {
  const svg = svgRef.value
  if (!svg) return { x: e.clientX, y: e.clientY }
  const rect = svg.getBoundingClientRect()
  return {
    x: (e.clientX - rect.left) / (rect.width / (layoutWidth.value / zoomLevel.value)) + offsetX.value,
    y: (e.clientY - rect.top) / (rect.height / (layoutHeight.value / zoomLevel.value)) + offsetY.value
  }
}

const selectedCompIds = ref<Set<string>>(new Set())
const isMarqueeSelecting = ref(false)
const marqueeStart = ref({ x: 0, y: 0 })
const marqueeEnd = ref({ x: 0, y: 0 })

const startMarquee = (e: MouseEvent) => {
  if (e.button !== 0) return
  if ((e.target as SVGElement).tagName === 'svg' || (e.target as SVGElement).tagName === 'rect') {
    const p = getSvgPoint(e)
    isMarqueeSelecting.value = true
    marqueeStart.value = p
    marqueeEnd.value = p
    window.addEventListener('mousemove', onMarqueeMove)
    window.addEventListener('mouseup', endMarquee)
  }
}
const onMarqueeMove = (e: MouseEvent) => {
  marqueeEnd.value = getSvgPoint(e)
}
const endMarquee = () => {
  if (isMarqueeSelecting.value) {
    const x1 = Math.min(marqueeStart.value.x, marqueeEnd.value.x)
    const y1 = Math.min(marqueeStart.value.y, marqueeEnd.value.y)
    const x2 = Math.max(marqueeStart.value.x, marqueeEnd.value.x)
    const y2 = Math.max(marqueeStart.value.y, marqueeEnd.value.y)
    selectedCompIds.value.clear()
    for (const comp of components.value) {
      const cx1 = comp.x
      const cy1 = comp.y
      const cx2 = comp.x + (comp.width || 0)
      const cy2 = comp.y + (comp.height || 0)
      if (cx1 >= x1 && cy1 >= y1 && cx2 <= x2 && cy2 <= y2) {
        selectedCompIds.value.add(comp.id)
      }
    }
  }
  isMarqueeSelecting.value = false
  window.removeEventListener('mousemove', onMarqueeMove)
  window.removeEventListener('mouseup', endMarquee)
}

const draggingId = ref<string | null>(null)
const startPos = ref({ x: 0, y: 0 })
const initialGroupPos = ref<{id: string,x: number,y:number}[]>([])
const getPolygonPoints = (comp: Component) =>
  comp.shapePoints ? comp.shapePoints.map(p => `${p.x},${p.y}`).join(' ') : ''

const updateTimers = new Map<string, number>()
const scheduleUpdateComponent = (compId: string, payload: any) => {
  if (updateTimers.has(compId)) clearTimeout(updateTimers.get(compId))
  const timer = window.setTimeout(() => {
    store.updateComponent(compId, payload)
    updateTimers.delete(compId)
  }, 300)
  updateTimers.set(compId, timer)
}

const startDrag = (e: MouseEvent, comp: Component) => {
  if (e.button !== 0) return
  e.stopPropagation()
  if (!selectedCompIds.value.has(comp.id)) {
    selectedCompIds.value.clear()
    selectedCompIds.value.add(comp.id)
  }
  draggingId.value = comp.id
  const p = getSvgPoint(e)
  startPos.value = { x: p.x, y: p.y }
  initialGroupPos.value = Array.from(selectedCompIds.value).map(id => {
    const c = components.value.find(co => co.id === id)!
    return { id, x: c.x, y: c.y }
  })
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', onDragUp)
}

const snapThreshold = 5
const snapLines = ref<{ x?: number; y?: number }>({})

const checkSnap = (comp: Component) => {
  snapLines.value = {}
  const xPositions: number[] = []
  const yPositions: number[] = []
  for (const c of components.value) {
    if (c.id === comp.id) continue
    const cx1 = c.x
    const cx2 = c.x + (c.width || 0)
    const cy1 = c.y
    const cy2 = c.y + (c.height || 0)
    const cxMid = c.x + (c.width || 0) / 2
    const cyMid = c.y + (c.height || 0) / 2
    xPositions.push(cx1, cx2, cxMid)
    yPositions.push(cy1, cy2, cyMid)
  }
  const compMidX = comp.x + (comp.width || 0) / 2
  for (const xp of xPositions) {
    if (Math.abs(comp.x - xp) < snapThreshold) {
      comp.x = xp
      snapLines.value.x = xp
    }
    if (Math.abs(compMidX - xp) < snapThreshold) {
      comp.x = xp - (comp.width || 0) / 2
      snapLines.value.x = xp
    }
  }
  const compMidY = comp.y + (comp.height || 0) / 2
  for (const yp of yPositions) {
    if (Math.abs(comp.y - yp) < snapThreshold) {
      comp.y = yp
      snapLines.value.y = yp
    }
    if (Math.abs(compMidY - yp) < snapThreshold) {
      comp.y = yp - (comp.height || 0) / 2
      snapLines.value.y = yp
    }
  }
}

const clampComp = (comp: Component) => {
  const minX = 0; // 左邊界
  const minY = 0; // 上邊界

  // ❌ 原本是減 comp.width/height，這會提前卡住
  // ✅ 改成直接用 layoutWidth/Height，或加容許超出
  const allowOverflow = 50; // 允許超出邊界的像素，可自行調整

  const maxX = layoutWidth.value + allowOverflow;
  const maxY = layoutHeight.value + allowOverflow;

  comp.x = Math.min(Math.max(comp.x, minX), maxX);
  comp.y = Math.min(Math.max(comp.y, minY), maxY);
}
const onDragMove = (e: MouseEvent) => {
  if (!draggingId.value) return
  const p = getSvgPoint(e)
  const dx = p.x - startPos.value.x
  const dy = p.y - startPos.value.y
  for (const init of initialGroupPos.value) {
    const comp = components.value.find(c => c.id === init.id)
    if (comp) {
      comp.x = init.x + dx
      comp.y = init.y + dy
      clampComp(comp)
      if (comp.id === draggingId.value) checkSnap(comp)
    }
  }
}
const onDragUp = () => {
  for (const id of selectedCompIds.value) {
    const comp = components.value.find(c => c.id === id)
    if (comp) scheduleUpdateComponent(id, { x: comp.x, y: comp.y })
  }
  snapLines.value = {}
  draggingId.value = null
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', onDragUp)
}

/* ==== Resize ==== */
const startResize = (e: MouseEvent, comp: Component, dir: 'nw' | 'ne' | 'sw' | 'se') => {
  e.stopPropagation()
  e.preventDefault()
  if (comp.shapePoints) return
  resizingId.value = comp.id
  resizeDir.value = dir
  const point = getSvgPoint(e)
  startSize.value = { x: point.x, y: point.y, width: comp.width!, height: comp.height! }
  window.addEventListener('mousemove', onResizeMove)
  window.addEventListener('mouseup', onResizeUp)
}

const onResizeMove = (e: MouseEvent) => {
  if (!resizingId.value || !resizeDir.value) return
  const comp = components.value.find(c => c.id === resizingId.value)
  if (!comp || comp.shapePoints) return
  const point = getSvgPoint(e)
  let dx = point.x - startSize.value.x
  let dy = point.y - startSize.value.y

  if (resizeDir.value === 'nw') {
    comp.width = Math.max(10, startSize.value.width - dx)
    comp.height = Math.max(10, startSize.value.height - dy)
    comp.x += dx
    comp.y += dy
  } else if (resizeDir.value === 'ne') {
    comp.width = Math.max(10, startSize.value.width + dx)
    comp.height = Math.max(10, startSize.value.height - dy)
    comp.y += dy
  } else if (resizeDir.value === 'sw') {
    comp.width = Math.max(10, startSize.value.width - dx)
    comp.height = Math.max(10, startSize.value.height + dy)
    comp.x += dx
  } else if (resizeDir.value === 'se') {
    comp.width = Math.max(10, startSize.value.width + dx)
    comp.height = Math.max(10, startSize.value.height + dy)
  }
}

const onResizeUp = () => {
  if (resizingId.value) {
    const comp = components.value.find(c => c.id === resizingId.value)
    if (comp) {
      scheduleUpdateComponent(comp.id, {
        x: comp.x, y: comp.y,
        width: comp.width, height: comp.height
      })
    }
  }
  resizingId.value = null
  resizeDir.value = null
  window.removeEventListener('mousemove', onResizeMove)
  window.removeEventListener('mouseup', onResizeUp)
}

/* ==== 新增/刪除 ==== */
const addRectBin = async () => { 
  if (layout.value) {
    await store.addComponent(layout.value.id, { 
      type: 'bin',
      x: layoutPaddingLeft,
      y: layoutPaddingTop,
      width: 150,
      height: 50,
      code: 'B-NEW',
      props: { color: '#475569' }
    })
  }
}

const addPolygonBin = async () => {
  if (!layout.value) return
  const points = [
    { x: 50, y: 0 }, { x: 100, y: 25 }, { x: 100, y: 75 },
    { x: 50, y: 100 }, { x: 0, y: 75 }, { x: 0, y: 25 }
  ]
  await store.addComponent(layout.value.id, {
    type: 'bin', 
    x: layoutPaddingLeft + 100,
    y: layoutPaddingTop + 100,
    width: 100,
    height: 100,
    code: 'POLY-BIN',
    shapePoints: points,
    props: { color: '#475569' }
  })
}

const addMachine = async () => { 
  if (layout.value) {
    await store.addComponent(layout.value.id, { 
      type: 'machine',
      x: layoutPaddingLeft + 250,
      y: layoutPaddingTop + 250,
      width: 150,
      height: 120,
      code: 'MC-NEW',
      props: { color: '#7c3aed' }
    })
  }
}
const deleteSelected = async () => {
  for (const id of selectedCompIds.value) await store.removeComponent(id)
  selectedCompIds.value.clear()
}

/* ==== MiniMap 視區計算 ==== */
const miniMapScale = computed(() => 200 / layoutWidth.value)
const viewBoxRect = computed(() => {
  const vw = Math.min(layoutWidth.value, layoutWidth.value / zoomLevel.value)
  const vh = Math.min(layoutHeight.value, layoutHeight.value / zoomLevel.value)
  const vx = Math.max(0, Math.min(layoutWidth.value - vw, offsetX.value))
  const vy = Math.max(0, Math.min(layoutHeight.value - vh, offsetY.value))
  return { x: vx, y: vy, width: vw, height: vh }
})

/* ==== 複製貼上 ==== */
const clipboardComponents = ref<Component[]>([])
const clipboardBasePos = ref<{x: number, y: number}>({x: 0, y: 0})
const mousePos = ref({ x: 0, y: 0 })

const onMouseMoveCanvas = (e: MouseEvent) => {
  mousePos.value = getSvgPoint(e)
}

const copySelected = () => {
  const comps: Component[] = Array.from(selectedCompIds.value)
    .map(id => {
      const comp = components.value.find(c => c.id === id)
      return comp ? JSON.parse(JSON.stringify(comp)) : null
    })
    .filter(Boolean) as Component[]

  if (comps.length > 0) {
    // 💡 先清空再覆蓋，確保不累積舊的
    clipboardComponents.value = []
    clipboardBasePos.value = { x: 0, y: 0 }
    
    clipboardComponents.value = comps
    const first = comps[0]
if (!first) return

clipboardBasePos.value = {
  x: first.x,
  y: first.y,
}
  }
}
const pasteAtCursor = async () => {
  if (!layout.value || clipboardComponents.value.length === 0) return
  const base = clipboardBasePos.value
  const cursor = mousePos.value

  for (const comp of clipboardComponents.value) {
    const dx = comp.x - base.x
    const dy = comp.y - base.y

    await store.addComponent(layout.value.id, {
      type: comp.type,
      x: cursor.x + dx,
      y: cursor.y + dy,
      width: comp.width || 0,
      height: comp.height || 0,
      code: comp.code + '-copy',
      shapePoints: comp.shapePoints ? comp.shapePoints.map(p => ({ x: p.x, y: p.y })) : undefined,
      props: { ...comp.props }
    })
  }
}

/* ==== 屬性編輯 & 儲存 ==== */
const selectedComponent = computed(() => {
  if (selectedCompIds.value.size === 1) {
    const id = [...selectedCompIds.value][0]
    return components.value.find(c => c.id === id) || null
  }
  return null
})

const saveProps = async () => {
  if (!selectedComponent.value) return
  const comp = selectedComponent.value
  const payload: Partial<Component> = {
    code: comp.code,
    x: comp.x,
    y: comp.y
  }
  if (!comp.shapePoints) {
    payload.width = comp.width
    payload.height = comp.height
  }
  await store.updateComponent(comp.id, payload)
}

const saveAll = async () => {
  if (!layout.value) return

  await store.updateLayout(layout.value.id, {
    width: layoutWidth.value,
    height: layoutHeight.value,
  })

  const tasks: Promise<any>[] = []
  for (const comp of components.value) {
    const payload: Partial<Component> = {
      code: comp.code,
      x: comp.x,
      y: comp.y,
    }
    if (!comp.shapePoints) {
      payload.width = comp.width
      payload.height = comp.height
    }
    tasks.push(store.updateComponent(comp.id, payload))
  }

  await Promise.all(tasks)
}

/* ==== 初始載入：抓資料＋fit layout＋快捷鍵 ==== */
onMounted(async () => {
  await store.fetchLayoutDetails(layoutId)
  await nextTick()
  fitToLayout()

  window.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'c') {
      e.preventDefault()
      copySelected()
    }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v') {
      e.preventDefault()
      pasteAtCursor()
    }
  })
})
</script>

<template>
  <div class="editor-container" v-if="layout">
    <aside class="sidebar">
      <div class="layout-settings">
        <h3>Layout 尺寸</h3>
        <div class="form-group-row">
          <div>
            <label>寬度</label>
            <input type="number" v-model.number="layoutWidth" />
          </div>
          <div>
            <label>高度</label>
            <input type="number" v-model.number="layoutHeight" />
          </div>
        </div>
      </div>

      <!-- 儲存按鈕 -->
      <button @click="saveAll" class="btn-save">💾 儲存</button>

      <h2>編輯器工具箱</h2>
      <div class="toolbox-actions">
        <button @click="copySelected" class="btn-tool">📄 複製選取</button>
        <button @click="pasteAtCursor" class="btn-tool">📋 貼上到游標</button>
        <button @click="addRectBin" class="btn-tool">□ 新增儲位</button>
        <button @click="addPolygonBin" class="btn-tool">⬡ 多邊形儲位</button>
        <button @click="addMachine" class="btn-tool">⚙ 新增機台</button>
      </div>

      <!-- 單選屬性 -->
      <div v-if="selectedCompIds.size === 1" class="properties-panel">
        <h3>屬性</h3>
        <template v-if="selectedComponent">
          <div class="form-group">
            <label>代碼</label>
            <input v-model="selectedComponent.code" @change="saveProps" />
          </div>
          <div class="form-group-row">
            <div>
              <label>X</label>
              <input type="number" v-model.number="selectedComponent.x" @change="saveProps" />
            </div>
            <div>
              <label>Y</label>
              <input type="number" v-model.number="selectedComponent.y" @change="saveProps" />
            </div>
          </div>
          <div v-if="!selectedComponent.shapePoints" class="form-group-row">
            <div>
              <label>W</label>
              <input type="number" v-model.number="selectedComponent.width" @change="saveProps" />
            </div>
            <div>
              <label>H</label>
              <input type="number" v-model.number="selectedComponent.height" @change="saveProps" />
            </div>
          </div>
        </template>
        <button @click="deleteSelected" class="btn-danger-outline">刪除元件</button>
      </div>

      <!-- 多選工具 -->
      <div v-else-if="selectedCompIds.size > 1" class="properties-panel">
        <h3>已選取 {{ selectedCompIds.size }} 個元件</h3>
        <button @click="deleteSelected" class="btn-danger-outline">刪除選取</button>
      </div>

      <div class="back-link">
        <router-link to="/">← 返回儀表板</router-link>
      </div>
    </aside>

     <section class="canvas-area"
      @mousedown="startPan"
      @mousemove="onPanMove"
      @mouseup="endPan"
      @mouseleave="endPan"
      @wheel="onWheelZoom"
      @contextmenu.prevent
      @mousedown.left="startMarquee">
      <div class="canvas-viewport">
        <svg ref="svgRef"
          :viewBox="`${offsetX} ${offsetY} ${layout.width / zoomLevel} ${layout.height / zoomLevel}`"
          @mousemove="onMouseMoveCanvas"
          :width="layout.width"
          :height="layout.height">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          <g v-for="comp in components" :key="comp.id" :class="{ selected: selectedCompIds.has(comp.id) }">
            <!-- 矩形元件 -->
            <rect v-if="!comp.shapePoints"
              :x="comp.x" :y="comp.y"
              :width="comp.width" :height="comp.height"
              class="comp-visual"
              @mousedown="startDrag($event, comp)" />
            
            <text v-if="!comp.shapePoints"
              :x="comp.x + comp.width/2"
              :y="comp.y + comp.height/2"
              class="label-center">{{ comp.code }}</text>

            <!-- 四角 Handle -->
            <template v-if="selectedCompIds.has(comp.id) && !comp.shapePoints">
              <rect class="handle nw"
                :x="comp.x - 4" :y="comp.y - 4"
                width="8" height="8"
                @mousedown.stop="startResize($event, comp, 'nw')" />
              <rect class="handle ne"
                :x="comp.x + comp.width - 4" :y="comp.y - 4"
                width="8" height="8"
                @mousedown.stop="startResize($event, comp, 'ne')" />
              <rect class="handle sw"
                :x="comp.x - 4" :y="comp.y + comp.height - 4"
                width="8" height="8"
                @mousedown.stop="startResize($event, comp, 'sw')" />
              <rect class="handle se"
                :x="comp.x + comp.width - 4" :y="comp.y + comp.height - 4"
                width="8" height="8"
                @mousedown.stop="startResize($event, comp, 'se')" />
            </template>

            <!-- 多邊形元件 -->
            <g v-if="comp.shapePoints"
              :transform="`translate(${comp.x}, ${comp.y})`"
              @mousedown="startDrag($event, comp)">
              <polygon :points="getPolygonPoints(comp)" class="comp-visual poly" />
              <text x="50" y="50" class="label-center">{{ comp.code }}</text>
            </g>
          </g>

          <!-- 吸附輔助線 -->
          <line v-if="snapLines.x !== undefined"
                :x1="snapLines.x" y1="0"
                :x2="snapLines.x" :y2="layoutHeight"
                stroke="red" stroke-width="1" stroke-dasharray="4" />
          <line v-if="snapLines.y !== undefined"
                x1="0" :y1="snapLines.y"
                :x2="layoutWidth" :y2="snapLines.y"
                stroke="red" stroke-width="1" stroke-dasharray="4" />

          <!-- 框選矩形 -->
          <rect v-if="isMarqueeSelecting"
            :x="Math.min(marqueeStart.x, marqueeEnd.x)"
            :y="Math.min(marqueeStart.y, marqueeEnd.y)"
            :width="Math.abs(marqueeEnd.x - marqueeStart.x)"
            :height="Math.abs(marqueeEnd.y - marqueeStart.y)"
            fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-dasharray="4" />
        </svg>
      </div>

      <!-- Mini Map -->
      <div class="mini-map">
        <svg :width="200" :height="layoutHeight * miniMapScale">
          <rect x="0" y="0"
                :width="layoutWidth * miniMapScale"
                :height="layoutHeight * miniMapScale"
                fill="#1e293b" stroke="#64748b" stroke-width="1"/>
          
          <g v-for="comp in components" :key="'mini-'+comp.id">
            <rect v-if="!comp.shapePoints"
                  :x="comp.x * miniMapScale" :y="comp.y * miniMapScale"
                  :width="comp.width * miniMapScale" :height="comp.height * miniMapScale"
                  fill="#64748b" stroke="#94a3b8" stroke-width="0.5"/>
            <g v-if="comp.shapePoints" :transform="`translate(${comp.x * miniMapScale}, ${comp.y * miniMapScale})`">
              <polygon :points="comp.shapePoints.map(p => `${p.x * miniMapScale},${p.y * miniMapScale}`).join(' ')" 
                       fill="#64748b" stroke="#94a3b8" stroke-width="0.5"/>
            </g>
          </g>

          <rect
            :x="viewBoxRect.x * miniMapScale"
            :y="viewBoxRect.y * miniMapScale"
            :width="viewBoxRect.width * miniMapScale"
            :height="viewBoxRect.height * miniMapScale"
            fill="rgba(59,130,246,0.2)"
            stroke="#3b82f6"
            stroke-width="1"
          />
        </svg>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ========= 版面結構 ========= */
.editor-container {
  flex: 1;
  display: flex;
  background: #0f172a;
  min-height: 0; /* 避免 flex 溢出 */
}

/* 左側工具箱：固定在左邊 320px 寬 */
.sidebar {
  width: 150px;
  background: rgba(30,41,59,0.5);
  border-right: 1px solid rgba(255,255,255,0.1);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
/* 編輯區：從 sidebar 右邊開始佔滿剩下寬度 */
.canvas-area {
  flex: 1;
  background: #0f172a;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
}

.canvas-area:active {
  cursor: grabbing;
}

/* 內部 SVG 容器 */
.canvas-viewport {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
}

/* Mini Map：相對於 canvas-area */
.mini-map {
  position: absolute;
  right: 10px;
  bottom: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(15, 23, 42, 0.8);
  padding: 4px;
}

/* ========= 元件顯示 ========= */
.comp-visual {
  fill: rgba(30, 41, 59, 0.8);
  stroke: rgba(255, 255, 255, 0.4);
  stroke-width: 1;
  cursor: move;
  transition: fill 0.2s;
}
.comp-visual:hover {
  fill: rgba(59, 130, 246, 0.4);
  stroke: #3b82f6;
}
.selected .comp-visual {
  stroke: #60a5fa;
  stroke-width: 2;
  filter: drop-shadow(0 0 5px rgba(59, 130, 246, 0.5));
}

/* 中央文字標籤 */
.label-center {
  fill: white;
  font-size: 12px;
  font-weight: 600;
  text-anchor: middle;
  dominant-baseline: central;
  pointer-events: none;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
}

/* Resize Handles */
.handle {
  fill: #3b82f6;
  stroke: white;
  stroke-width: 1;
  cursor: pointer;
}
.handle:hover {
  fill: white;
  stroke: #3b82f6;
}
.handle.nw,
.handle.se {
  cursor: nwse-resize;
}
.handle.ne,
.handle.sw {
  cursor: nesw-resize;
}

/* ========= Sidebar 內容 ========= */
.properties-panel {
  margin-top: 2rem;
}

.back-link {
  margin-top: auto;
}
.back-link a {
  color: #94a3b8;
  text-decoration: none;
}

/* ========= 按鈕 / 表單 ========= */
.btn-tool {
  width: 100%;
  padding: 0.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 0.5rem;
}

.btn-save {
  width: 100%;
  padding: 0.75rem;
  margin: 0 0 1rem 0;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}
.btn-save:hover {
  background: #059669;
}

.btn-danger-outline {
  border: 1px solid #ef4444;
  color: #ef4444;
  background: transparent;
  width: 100%;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 4px;
}

.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #94a3b8;
}
.form-group input {
  width: 100%;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: 4px;
}

.form-group-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}
.form-group-row input {
  width: 100%;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: 4px;
}
</style>
