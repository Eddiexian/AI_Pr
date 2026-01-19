<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWarehouseStore, type Component } from '../stores/warehouse'

const route = useRoute()
const router = useRouter()
const store = useWarehouseStore()
const layoutId = route.params.id as string

onMounted(async () => {
    await store.fetchLayoutDetails(layoutId)
})

const layout = computed(() => store.currentLayout)
const components = computed(() => layout.value?.components || [])
const selectedComp = ref<Component | null>(null)
const wipData = ref<any>(null)
const searchQuery = ref('')
const searchResult = ref<string | null>(null)

// Find WIP Logic
// 搜尋定位邏輯 (Search & Positioning Logic)
const handleSearch = async () => {
  if (!searchQuery.value) return
  // 邏輯: 1. 若輸入為儲位代碼則直接定位 2. 若為 Sheet ID 則模擬搜尋 (Mock)
  let targetCode = searchQuery.value.trim().toUpperCase()
  
  const foundByCode = components.value.find(c => c.code?.toUpperCase() === targetCode)
  if (foundByCode) {
    handleCompClick(foundByCode)
    searchResult.value = foundByCode.code
  } else {
    // 模擬 Sheet 搜尋: 若包含 "S" 則隨機指向一個有 WIP 的儲位
    const mockBin = components.value.find(c => c.type === 'bin')
    if (mockBin) {
      handleCompClick(mockBin)
      searchResult.value = mockBin.code
    }
  }
}

// Helper: Polygons
const getPolygonPoints = (comp: Component) => {
    if (!comp.shapePoints) return ''
    return comp.shapePoints.map(p => `${p.x},${p.y}`).join(' ')
}

// Interaction
const handleCompClick = async (comp: Component) => {
    selectedComp.value = comp
    searchResult.value = null // clear search highlight
    // Fetch Data
    wipData.value = null // Reset
    if (comp.code) {
        const data = await store.fetchWipData([comp.code])
        wipData.value = data[comp.code] || []
    }
}

const closeDetail = () => {
    selectedComp.value = null
    wipData.value = null
}

// 獲取儲位填滿顏色 (Get Fill Color based on status)
const getFillColor = (comp: Component) => {
    // 搜尋高亮 (Search matching)
    if (searchResult.value === comp.code) return '#fbbf24' // Highlight yellow
    
    // 根據數量顯示不同警示色 (Alert colors based on box count)
    const count = store.binCounts[comp.code || ''] || 0
    if (count > 3) return 'rgba(239, 68, 68, 0.7)' // 數量過多 (Critical)
    if (count > 0) return 'rgba(16, 185, 129, 0.7)' // 正常 (Healthy)
    
    // Determine color based on status (Requires backend status calculation or separate status map)
    // For now, random/hashed status or simple check
    // In real app, we might merge dynamic status into components
    if (comp.props?.color) return comp.props.color
    return 'rgba(30, 41, 59, 0.6)'
}

</script>

<template>
  <div class="operation-container" v-if="layout">
    <div class="top-bar">
        <button @click="router.push('/')" class="btn-back">← 返回</button>
        <span class="layout-title">{{ layout.name }} - 作業模式</span>
        
        <div class="search-box">
          <input v-model="searchQuery" placeholder="搜尋 Sheet ID..." @keyup.enter="handleSearch" />
          <button @click="handleSearch" class="btn-search">定位儲位</button>
        </div>
    </div>

    <main class="canvas-area">
      <div class="canvas-viewport" :style="{ width: layout.width + 'px', height: layout.height + 'px' }">
        <svg width="100%" height="100%">
             <!-- Render Components -->
            <g v-for="comp in components" :key="comp.id" 
               @click="handleCompClick(comp)"
               class="comp-group"
               :class="{ highlighted: searchResult === comp.code }"
            >
                <rect 
                    v-if="!comp.shapePoints"
                    :x="comp.x" :y="comp.y" 
                    :width="comp.width" :height="comp.height"
                    class="comp-visual"
                    :class="comp.type"
                    :fill="getFillColor(comp)"
                />
                
                <g v-if="comp.shapePoints" :transform="`translate(${comp.x}, ${comp.y})`">
                    <polygon :points="getPolygonPoints(comp)" class="comp-visual" :class="comp.type" :fill="getFillColor(comp)"/>
                </g>
                
                <!-- Icons/Text for different types -->
                <text v-if="comp.type === 'machine'" :x="comp.x + comp.width/2" :y="comp.y + comp.height/2 + 5" fill="white" font-size="20" text-anchor="middle" pointer-events="none" style="opacity: 0.3">⚙</text>
                <text v-if="comp.type === 'pillar'" :x="comp.x + comp.width/2" :y="comp.y + comp.height/2 + 5" fill="white" font-size="12" text-anchor="middle" pointer-events="none" style="opacity: 0.3">柱</text>
                
                <!-- Label & Box Count Badge -->
                <text :x="comp.x + 5" :y="comp.y + 15" fill="white" font-size="10" pointer-events="none" class="comp-label">{{ comp.code }}</text>
                
                <g v-if="comp.type === 'bin' && store.binCounts[comp.code || '']" class="count-badge">
                   <circle :cx="comp.x + comp.width" :cy="comp.y" r="10" fill="#ef4444" />
                   <text :x="comp.x + comp.width" :y="comp.y + 4" fill="white" font-size="10" text-anchor="middle" font-weight="bold">{{ store.binCounts[comp.code || ''] }}</text>
                </g>
            </g>
        </svg>
      </div>
    </main>

    <!-- Detail Panel -->
    <div v-if="selectedComp" class="detail-overlay" @click.self="closeDetail">
      <div class="detail-card glass-panel">
        <button class="close-btn" @click="closeDetail">×</button>
        <h2>儲位: {{ selectedComp.code }}</h2>
        
        <div class="data-section">
           <h3>WIP 資訊</h3>
           <div v-if="!wipData || wipData.length === 0" class="empty-msg">查無資料</div>
           
           <div v-else class="ppbox-list">
             <div v-for="cst in wipData" :key="cst.cassette_id" class="ppbox-item">
                <div class="box-header">
                    <span>📦 {{ cst.cassette_id }}</span>
                    <span class="pos-tag">Pos: {{ cst.position }}</span>
                </div>
                <table class="wip-table">
                    <thead><tr><th>Chip ID</th><th>Grade</th><th>Model</th><th>Stage</th></tr></thead>
                    <tbody>
                        <tr v-for="wip in cst.wips" :key="wip.sheet_id_chip_id">
                            <td>{{ wip.sheet_id_chip_id }}</td>
                            <td>{{ wip.grade }}</td>
                            <td>{{ wip.model_no }}</td>
                            <td>{{ wip.stage_id }}</td>
                        </tr>
                    </tbody>
                </table>
             </div>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.operation-container { display: flex; flex-direction: column; height: calc(100vh - 60px); }
.top-bar { padding: 1rem; background: rgba(30,41,59,0.5); display: flex; gap: 1rem; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
.canvas-area { flex: 1; background: #0f172a; display: flex; justify-content: center; align-items: center; overflow: auto; }
.canvas-viewport { box-shadow: 0 0 30px rgba(0,0,0,0.5); background: rgba(255,255,255,0.02); }
.comp-visual { stroke: rgba(255,255,255,0.3); stroke-width: 1; cursor: pointer; transition: all 0.2s; }
.comp-visual:hover { stroke: #60a5fa; stroke-width: 2; filter: brightness(1.2); }
.detail-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 50; }
.detail-card { width: 600px; max-height: 80vh; overflow-y: auto; background: #1e293b; padding: 2rem; border-radius: 12px; position: relative; color: white; }
.close-btn { position: absolute; right: 1rem; top: 1rem; background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; }
.ppbox-item { margin-bottom: 1rem; background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 6px; }
.box-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-weight: bold; color: #fbbf24; }
.wip-table { width: 100%; font-size: 0.9rem; border-collapse: collapse; }
.wip-table th { text-align: left; color: #94a3b8; border-bottom: 1px solid #475569; padding: 0.5rem; }
.wip-table td { padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
.btn-back { background: transparent; border: 1px solid #475569; color: white; padding: 0.5rem; border-radius: 4px; cursor: pointer; }

.search-box {
  margin-left: auto;
  display: flex;
  gap: 0.5rem;
}
.search-box input {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  padding: 0.5rem;
  border-radius: 4px;
  width: 200px;
}
.btn-search {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
.highlighted .comp-visual {
  stroke: #fbbf24;
  stroke-width: 3;
  filter: drop-shadow(0 0 10px #fbbf24);
}
.comp-label {
  text-shadow: 1px 1px 2px black;
}
</style>
