<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWarehouseStore, type Component } from '../stores/warehouse'

const route = useRoute()
const router = useRouter()
const store = useWarehouseStore()
const layoutId = route.params.id as string

// Load Layout
onMounted(async () => {
    await store.fetchLayoutDetails(layoutId)
})

const layout = computed(() => store.currentLayout)
const components = computed(() => layout.value?.components || [])

const selectedCompId = ref<string | null>(null)
const selectedComp = computed(() => components.value.find(c => c.id === selectedCompId.value))

// 拖拽與縮放狀態 (Drag & Resize State)
const draggingId = ref<string|null>(null)
const startPos = ref({ x: 0, y: 0 })
const initialCompPos = ref({ x: 0, y: 0 })

// Helper: Convert ShapePoints to SVG String
const getPolygonPoints = (comp: Component) => {
    if (!comp.shapePoints) return ''
    return comp.shapePoints.map(p => `${p.x},${p.y}`).join(' ')
}

// 新增矩形儲位 (Add Rectangular Bin)
const addRectBin = async () => {
    if (!layout.value) return
    await store.addComponent(layout.value.id, {
        type: 'bin',
        x: 50, y: 50, width: 100, height: 100,
        code: 'B-NEW',
        props: { color: '#475569' } // Default Slate-600
    })
}

// 新增多邊形儲位 (Add Polygon Bin)
    // Standard Hexagon for demo
    if (!layout.value) return
    const points = [
        {x: 50, y: 0}, {x: 100, y: 25}, {x: 100, y: 75},
        {x: 50, y: 100}, {x: 0, y: 75}, {x: 0, y: 25}
    ]
    await store.addComponent(layout.value.id, {
        type: 'bin',
        x: 150, y: 150, width: 100, height: 100, // Bounding box for reference
        code: 'POLY-BIN',
        shapePoints: points,
        props: { color: '#475569' }
    })
}

const addMachine = async () => {
    if (!layout.value) return
    await store.addComponent(layout.value.id, {
        type: 'machine',
        x: 300, y: 300, width: 150, height: 120,
        code: 'MC-NEW',
        props: { color: '#7c3aed' } // Violet-600
    })
}

// Selection
const selectComp = (id: string) => {
    selectedCompId.value = id
}

// Drag Logic (for Rects primarily)
const startDrag = (e: MouseEvent, comp: Component) => {
    if (e.button !== 0) return // Left click only
    e.stopPropagation()
    draggingId.value = comp.id
    startPos.value = { x: e.clientX, y: e.clientY }
    initialCompPos.value = { x: comp.x, y: comp.y }
    
    window.addEventListener('mousemove', onDragMove)
    window.addEventListener('mouseup', onDragUp)
}

// 處理組件拖拽 (Handle Component Dragging)
const onDragMove = (e: MouseEvent) => {
    if (!draggingId.value) return
    
    // 使用 requestAnimationFrame 提升拖拽流暢度 (Smooth dragging)
    requestAnimationFrame(() => {
        const dx = e.clientX - startPos.value.x
        const dy = e.clientY - startPos.value.y
        
        const comp = components.value.find(c => c.id === draggingId.value)
        if (comp) {
            comp.x = initialCompPos.value.x + dx
            comp.y = initialCompPos.value.y + dy
        }
    })
}

const onDragUp = async () => {
    if (draggingId.value) {
        const comp = components.value.find(c => c.id === draggingId.value)
        if (comp) {
            // 保存位置變更至後端 (Persist position)
            await store.updateComponent(comp.id, { x: comp.x, y: comp.y })
        }
    }
    draggingId.value = null
    window.removeEventListener('mousemove', onDragMove)
    window.removeEventListener('mouseup', onDragUp)
}

// 縮放邏輯 (Resizing Logic)
const resizingId = ref<string | null>(null)
const resizeHandle = ref<string | null>(null)
const initialDim = ref({ w: 0, h: 0 })

// 開始縮放 (Start Resizing)
const startResize = (e: MouseEvent, comp: Component, handle: string) => {
    e.stopPropagation()
    resizingId.value = comp.id
    resizeHandle.value = handle
    startPos.value = { x: e.clientX, y: e.clientY }
    initialCompPos.value = { x: comp.x, y: comp.y }
    initialDim.value = { w: comp.width, h: comp.height }
    
    window.addEventListener('mousemove', onResizeMove)
    window.addEventListener('mouseup', onResizeUp)
}

const onResizeMove = (e: MouseEvent) => {
    if (!resizingId.value) return
    
    requestAnimationFrame(() => {
        const dx = e.clientX - startPos.value.x
        const dy = e.clientY - startPos.value.y
        const comp = components.value.find(c => c.id === resizingId.value)
        if (!comp) return

        // 根據把手方位調整寬高與坐標 (Adjust dims based on handle direction)
        if (resizeHandle.value?.includes('e')) {
            comp.width = Math.max(20, initialDim.value.w + dx)
        }
        if (resizeHandle.value?.includes('w')) {
            const newW = Math.max(20, initialDim.value.w - dx)
            if (newW > 20) {
                comp.width = newW
                comp.x = initialCompPos.value.x + dx
            }
        }
        if (resizeHandle.value?.includes('s')) {
            comp.height = Math.max(20, initialDim.value.h + dy)
        }
        if (resizeHandle.value?.includes('n')) {
            const newH = Math.max(20, initialDim.value.h - dy)
            if (newH > 20) {
                comp.height = newH
                comp.y = initialCompPos.value.y + dy
            }
        }
    })
}

const onResizeUp = async () => {
    if (resizingId.value) {
        const comp = components.value.find(c => c.id === resizingId.value)
        if (comp) {
            await store.updateComponent(comp.id, { 
                x: comp.x, y: comp.y, 
                width: comp.width, height: comp.height 
            })
        }
    }
    resizingId.value = null
    resizeHandle.value = null
    window.removeEventListener('mousemove', onResizeMove)
    window.removeEventListener('mouseup', onResizeUp)
}

// Delete
const deleteSelected = async () => {
    if (selectedCompId.value) {
        await store.removeComponent(selectedCompId.value)
        selectedCompId.value = null
    }
}

// Save Props
const saveProps = async () => {
    if (selectedComp.value) {
        await store.updateComponent(selectedComp.value.id, {
            code: selectedComp.value.code,
            width: selectedComp.value.width,
            height: selectedComp.value.height
        })
    }
}

</script>

<template>
  <div class="editor-container" v-if="layout">
    <aside class="sidebar">
      <h2>編輯器工具箱</h2>
      <div class="toolbox-actions">
        <button @click="addRectBin" class="btn-tool">□ 新增儲位 (Bin)</button>
        <button @click="addPolygonBin" class="btn-tool">⬡ 多邊形儲位 (Poly)</button>
        <button @click="addMachine" class="btn-tool">⚙ 新增機台 (Machine)</button>
      </div>

      <div v-if="selectedComp" class="properties-panel">
        <h3>屬性 (Properties)</h3>
        <div class="form-group">
          <label>代碼 (Code)</label>
          <input v-model="selectedComp.code" @change="saveProps"/>
        </div>
        <div class="form-group-row">
            <div>
               <label>X</label>
               <input type="number" v-model.number="selectedComp.x" @change="saveProps" />
            </div>
            <div>
               <label>Y</label>
               <input type="number" v-model.number="selectedComp.y" @change="saveProps" />
            </div>
        </div>
        
        <div v-if="!selectedComp.shapePoints" class="form-group-row">
            <div>
               <label>W</label>
               <input type="number" v-model.number="selectedComp.width" @change="saveProps" />
            </div>
            <div>
               <label>H</label>
               <input type="number" v-model.number="selectedComp.height" @change="saveProps" />
            </div>
        </div>

        <button @click="deleteSelected" class="btn-danger-outline">刪除元件</button>
      </div>
      <div class="back-link">
        <router-link to="/">← 返回儀表板</router-link>
      </div>
    </aside>

    <main class="canvas-area">
      <div class="canvas-viewport" :style="{ width: layout.width + 'px', height: layout.height + 'px' }">
        <svg width="100%" height="100%">
            <!-- Grid Lines (Optional) -->
            <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />

            <!-- Render Components -->
            <g v-for="comp in components" :key="comp.id" 
               @mousedown="selectComp(comp.id)"
               :class="{ selected: selectedCompId === comp.id }"
            >
                <!-- Rectangular Component -->
                <rect 
                    v-if="!comp.shapePoints"
                    :x="comp.x" :y="comp.y" 
                    :width="comp.width" :height="comp.height"
                    class="comp-visual"
                    @mousedown="startDrag($event, comp)" 
                />
                <text 
                    v-if="!comp.shapePoints" 
                    :x="comp.x + comp.width / 2" 
                    :y="comp.y + comp.height / 2" 
                    class="label-center"
                >{{ comp.code }}</text>

                <!-- Polygon Component -->
                <g v-if="comp.shapePoints" :transform="`translate(${comp.x}, ${comp.y})`" @mousedown="startDrag($event, comp)">
                    <polygon :points="getPolygonPoints(comp)" class="comp-visual poly" />
                    <!-- Center for polygon: using simple average of bounds for now -->
                    <text 
                        x="50" y="50" 
                        class="label-center"
                    >{{ comp.code }}</text>
                </g>

                <!-- Resize Handles (Only for non-polygons and when selected) -->
                <g v-if="selectedCompId === comp.id && !comp.shapePoints" class="resize-handles">
                  <circle :cx="comp.x" :cy="comp.y" r="5" class="handle nw" @mousedown="startResize($event, comp, 'nw')" />
                  <circle :cx="comp.x + comp.width" :cy="comp.y" r="5" class="handle ne" @mousedown="startResize($event, comp, 'ne')" />
                  <circle :cx="comp.x" :cy="comp.y + comp.height" r="5" class="handle sw" @mousedown="startResize($event, comp, 'sw')" />
                  <circle :cx="comp.x + comp.width" :cy="comp.y + comp.height" r="5" class="handle se" @mousedown="startResize($event, comp, 'se')" />
                </g>
            </g>
        </svg>
      </div>
    </main>
  </div>
</template>

<style scoped>
.editor-container {
  display: flex;
  height: calc(100vh - 60px);
}
.sidebar {
  width: 320px;
  background: rgba(30, 41, 59, 0.5);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}
.canvas-area {
  flex: 1;
  background: #0f172a;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
}
.canvas-viewport {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 30px rgba(0,0,0,0.5);
}
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
.properties-panel { margin-top: 2rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; color: #94a3b8; }
.form-group input { width: 100%; padding: 0.5rem; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: white; border-radius: 4px; }
.form-group-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
.form-group-row input { width: 100%; padding: 0.5rem; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); color: white; border-radius: 4px; }
.btn-danger-outline { border: 1px solid #ef4444; color: #ef4444; background: transparent; width: 100%; padding: 0.5rem; cursor: pointer; border-radius: 4px; }
.back-link { margin-top: auto; }
.back-link a { color: #94a3b8; text-decoration: none; }
.label-center {
  fill: white;
  font-size: 12px;
  font-weight: 600;
  text-anchor: middle;
  dominant-baseline: central;
  pointer-events: none;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
}

.handle {
  fill: #3b82f6;
  stroke: white;
  stroke-width: 1;
  cursor: pointer;
}
.handle:hover { fill: white; stroke: #3b82f6; }
.handle.nw, .handle.se { cursor: nwse-resize; }
.handle.ne, .handle.sw { cursor: nesw-resize; }
</style>
