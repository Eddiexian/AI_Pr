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

const selectedBin = ref<Bin | null>(null)

if (!layout.value) {
  router.push('/')
}

const handleBinClick = (bin: Bin) => {
  // Demo: inject mock data if empty
  store.mockBinData(bin.id)
  selectedBin.value = bin
}

const closeDetail = () => {
  selectedBin.value = null
}
</script>

<template>
  <div class="operation-container" v-if="layout">
    <div class="top-bar">
        <button @click="router.push('/')" class="btn-back">← 返回儀表板</button>
        <span class="layout-title">{{ layout.name }} - 作業模式</span>
    </div>

    <main class="canvas-area">
      <div class="canvas-viewport" :style="{ width: layout.width + 'px', height: layout.height + 'px' }">
        <div 
          v-for="bin in bins" 
          :key="bin.id"
          class="bin-wrapper"
          :style="{ transform: `translate(${bin.x}px, ${bin.y}px)` }"
        >
           <div 
             class="bin-visual"
             :class="bin.status"
             :style="{ width: bin.w + 'px', height: bin.h + 'px' }"
             @click="handleBinClick(bin)"
           >
             {{ bin.code }}
           </div>
        </div>
      </div>
    </main>

    <!-- Modal/Panel for Details -->
    <div v-if="selectedBin" class="detail-overlay" @click.self="closeDetail">
      <div class="detail-card glass-panel">
        <button class="close-btn" @click="closeDetail">×</button>
        <h2>儲位代碼: {{ selectedBin.code }}</h2>
        
        <div class="detail-grid">
          <div class="detail-item">
             <label>狀態 (Status)</label>
             <span class="status-badge" :class="selectedBin.status">{{ selectedBin.status }}</span>
          </div>
          <div class="detail-item">
             <label>座標 (Coord)</label>
             <span>X: {{ Math.round(selectedBin.x) }}, Y: {{ Math.round(selectedBin.y) }}</span>
          </div>
        </div>

        <div class="data-section">
           <h3>庫存清單 (Inventory)</h3>
           <div v-if="!selectedBin.contents || selectedBin.contents.length === 0" class="empty-msg">
             此儲位目前無資料。
           </div>
           
           <div v-else class="ppbox-list">
             <div v-for="box in selectedBin.contents" :key="box.id" class="ppbox-item">
                <div class="box-header">
                    <span class="box-icon">📦</span>
                    <span class="box-id">{{ box.box_id }}</span>
                </div>
                <!-- WIP Table -->
                <table class="wip-table">
                    <thead>
                        <tr>
                            <th>WIP ID</th>
                            <th>Model</th>
                            <th>Grade</th>
                            <th>OP</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="wip in box.wips" :key="wip.id">
                            <td>{{ wip.id }}</td>
                            <td>{{ wip.model }}</td>
                            <td><span class="grade-tag">{{ wip.grade }}</span></td>
                            <td>{{ wip.op_id }}</td>
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
.operation-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  position: relative;
}

.top-bar {
    padding: 1rem 2rem;
    background: rgba(30, 41, 59, 0.5);
    display: flex;
    align-items: center;
    gap: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.btn-back {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.2);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    cursor: pointer;
}

.canvas-area {
  flex: 1;
  background: #0f172a;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 50px;
}

.canvas-viewport {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  position: relative;
  box-shadow: 0 0 30px rgba(0,0,0,0.5);
}

.bin-wrapper {
  position: absolute;
  top: 0;
  left: 0;
}

.bin-visual {
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(30, 41, 59, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.bin-visual:hover {
  transform: scale(1.05);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
  border-color: #3b82f6;
  z-index: 10;
}

.bin-visual.occupied { background: rgba(220, 38, 38, 0.4); border-color: rgba(220, 38, 38, 0.6); }
.bin-visual.reserved { background: rgba(234, 179, 8, 0.4); border-color: rgba(234, 179, 8, 0.6); }
.bin-visual.empty { background: rgba(16, 185, 129, 0.3); border-color: rgba(16, 185, 129, 0.5); }

/* Modal/Overlay */
.detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-card {
  width: 600px; /* Wider for table */
  max-height: 80vh;
  overflow-y: auto;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 2rem;
  position: relative;
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.5rem;
  cursor: pointer;
}

.detail-grid {
  display: flex;
  gap: 2rem;
  margin: 1.5rem 0;
  background: rgba(255,255,255,0.03);
  padding: 1rem;
  border-radius: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-item label {
  color: #94a3b8;
  font-size: 0.8rem;
  margin-bottom: 0.2rem;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  text-transform: uppercase;
  font-weight: 700;
  display: inline-block;
}

.status-badge.occupied { background: rgba(220,38,38,0.2); color: #f87171; }
.status-badge.empty { background: rgba(16,185,129,0.2); color: #34d399; }
.status-badge.reserved { background: rgba(234,179,8,0.2); color: #facc15; }

.ppbox-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.ppbox-item {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid rgba(255,255,255,0.1);
}

.box-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-weight: 700;
    color: #ffd700;
}

.wip-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.wip-table th {
    text-align: left;
    color: #94a3b8;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 0.5rem;
}

.wip-table td {
    padding: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.grade-tag {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.8rem;
}
</style>
