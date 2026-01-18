<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWarehouseStore, type Bin } from '../stores/warehouse'

const route = useRoute()
const router = useRouter()
const store = useWarehouseStore()
const layoutId = route.params.id as string

const layout = computed(() => store.layouts.find(l => l.id === layoutId))
const bins = store.getBinsByLayout(layoutId)

const selectedBinId = ref<string | null>(null)
const selectedBin = computed(() => bins.value.find(b => b.id === selectedBinId.value))

const draggingBinId = ref<string|null>(null)
const resizingBinId = ref<string|null>(null)

if (!layout.value) {
  router.push('/')
}

const addBin = () => {
  const id = store.addBin(layoutId, 50, 50)
  selectedBinId.value = id
}

const deleteSelected = () => {
  if (selectedBinId.value) {
    store.removeBin(selectedBinId.value)
    selectedBinId.value = null
  }
}

// Drag logic
const startDrag = (e: MouseEvent, bin: Bin) => {
  e.preventDefault()
  e.stopPropagation()
  selectedBinId.value = bin.id
  draggingBinId.value = bin.id
  
  const startX = e.clientX - bin.x
  const startY = e.clientY - bin.y
  
  const moveHandler = (me: MouseEvent) => {
    store.updateBin(bin.id, {
      x: me.clientX - startX,
      y: me.clientY - startY
    })
  }
  
  const upHandler = () => {
    draggingBinId.value = null
    document.removeEventListener('mousemove', moveHandler)
    document.removeEventListener('mouseup', upHandler)
  }
  
  document.addEventListener('mousemove', moveHandler)
  document.addEventListener('mouseup', upHandler)
}

// Resize logic
const startResize = (e: MouseEvent, bin: Bin) => {
  e.preventDefault()
  e.stopPropagation()
  resizingBinId.value = bin.id
  
  const startX = e.clientX
  const startY = e.clientY
  const startW = bin.w
  const startH = bin.h
  
  const moveHandler = (me: MouseEvent) => {
    const w = Math.max(20, startW + (me.clientX - startX))
    const h = Math.max(20, startH + (me.clientY - startY))
    store.updateBin(bin.id, { w, h })
  }
  
  const upHandler = () => {
    resizingBinId.value = null
    document.removeEventListener('mousemove', moveHandler)
    document.removeEventListener('mouseup', upHandler)
  }
  
  document.addEventListener('mousemove', moveHandler)
  document.addEventListener('mouseup', upHandler)
}

const updateLayoutSize = () => {
    // Already reactive via v-model on store object
}

</script>

<template>
  <div class="editor-container" v-if="layout">
    <aside class="sidebar">
      <h2>編輯器工具箱 (Toolbox)</h2>
      <div class="toolbox-actions">
        <button @click="addBin" class="btn-tool">+ 新增儲位 (Add Bin)</button>
      </div>

      <div class="layout-props">
          <h3>版面設定 (Layout)</h3>
           <div class="form-group-row">
             <div>
                <label>寬度</label>
                <input type="number" v-model="layout.width" />
             </div>
             <div>
                <label>高度</label>
                <input type="number" v-model="layout.height" />
             </div>
           </div>
      </div>
      
      <div v-if="selectedBin" class="properties-panel">
        <h3>儲位屬性 (Properties)</h3>
        <div class="form-group">
          <label>代碼 (Code)</label>
          <input v-model="selectedBin.code" />
        </div>
        <div class="form-group-row">
            <div>
              <label>寬 (W)</label>
              <input type="number" v-model.number="selectedBin.w" />
            </div>
            <div>
              <label>高 (H)</label>
              <input type="number" v-model.number="selectedBin.h" />
            </div>
        </div>
        <div class="form-group-row">
            <div>
              <label>X 座標</label>
              <input type="number" v-model.number="selectedBin.x" />
            </div>
            <div>
              <label>Y 座標</label>
              <input type="number" v-model.number="selectedBin.y" />
            </div>
        </div>
         <div class="form-group">
          <label>狀態 (Status)</label>
          <select v-model="selectedBin.status">
            <option value="empty">空儲位 (Empty)</option>
            <option value="occupied">有貨 (Occupied)</option>
            <option value="reserved">預約 (Reserved)</option>
          </select>
        </div>
        <button @click="deleteSelected" class="btn-danger-outline">刪除儲位</button>
      </div>
      <div v-else class="properties-empty">
        <p>請點選儲位以編輯內容</p>
      </div>

      <div class="back-link">
        <router-link to="/">← 返回儀表板</router-link>
      </div>
    </aside>

    <main class="canvas-area">
      <div class="canvas-wrapper">
        <div class="canvas-viewport" :style="{ width: layout.width + 'px', height: layout.height + 'px' }">
            <!-- Render Bins -->
            <div 
            v-for="bin in bins" 
            :key="bin.id"
            class="draggable-bin-wrapper"
            :class="{ 
                'selected': selectedBinId === bin.id,
                'dragging': draggingBinId === bin.id
            }"
            :style="{ transform: `translate(${bin.x}px, ${bin.y}px)` }"
            @mousedown.stop="startDrag($event, bin)"
            >
            <div 
                class="bin-visual"
                :class="bin.status"
                :style="{ width: bin.w + 'px', height: bin.h + 'px' }"
            >
                <div class="bin-label">{{ bin.code }}</div>
                
                <!-- Resize Handle -->
                <div 
                    class="resize-handle"
                    @mousedown.stop="startResize($event, bin)"
                ></div>
            </div>
            </div>
        </div>
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
  overflow-y: auto;
}

.canvas-area {
  flex: 1;
  background: #0f172a;
  overflow: hidden; /* Handle inner scroll */
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.canvas-wrapper {
    width: 100%;
    height: 100%;
    overflow: auto;
    padding: 100px;
    display: flex; /* Centers content if smaller than viewport */
}

.canvas-viewport {
  background: rgba(255, 255, 255, 0.03);
  background-image: 
    linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 50px rgba(0,0,0,0.5);
  position: relative;
  flex-shrink: 0; /* Prevent shrinking */
  transition: width 0.3s, height 0.3s;
}

.draggable-bin-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  cursor: grab;
  user-select: none;
}

.draggable-bin-wrapper.dragging {
    cursor: grabbing;
    opacity: 0.8;
}

.draggable-bin-wrapper.selected {
    z-index: 100;
}

.draggable-bin-wrapper.selected .bin-visual {
  border-color: #60a5fa; /* Blue-400 */
  box-shadow: 0 0 0 2px #3b82f6;
}

.bin-visual {
  border: 1px solid rgba(255,255,255,0.3);
  background: rgba(30, 41, 59, 0.8);
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.bin-label {
    padding: 4px;
    text-align: center;
    word-break: break-all;
    pointer-events: none;
}

.resize-handle {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 10px;
    height: 10px;
    background: rgba(255,255,255,0.5);
    cursor: nwse-resize;
    display: none; /* Show only on hover/selected */
}

.draggable-bin-wrapper.selected .resize-handle,
.draggable-bin-wrapper:hover .resize-handle {
    display: block;
}

.bin-visual.occupied { background: rgba(220, 38, 38, 0.4); border-color: rgba(220, 38, 38, 0.6); }
.bin-visual.reserved { background: rgba(234, 179, 8, 0.4); border-color: rgba(234, 179, 8, 0.6); }
.bin-visual.empty { background: rgba(16, 185, 129, 0.3); border-color: rgba(16, 185, 129, 0.5); }

/* Sidebar UI */
h2, h3 {
    margin-top: 0;
    color: #e2e8f0;
}

h3 {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    margin-top: 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 0.5rem;
}

.toolbox-actions { margin-bottom: 1rem; }

.btn-tool {
  width: 100%;
  padding: 0.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.form-group, .form-group-row {
  margin-bottom: 1rem;
}

.form-group-row {
    display: flex;
    gap: 1rem;
}

.form-group-row > div { flex: 1; }

label {
  display: block;
  font-size: 0.8rem;
  color: #94a3b8;
  margin-bottom: 0.3rem;
}

input, select {
  width: 100%;
  padding: 0.5rem;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.1);
  color: white;
  border-radius: 4px;
}

.btn-danger-outline {
  width: 100%;
  padding: 0.5rem;
  background: transparent;
  border: 1px solid #ef4444;
  color: #ef4444;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
}

.back-link {
  margin-top: auto;
  padding-top: 2rem;
}

.back-link a {
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.9rem;
}
</style>
