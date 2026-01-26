<script setup lang="ts">
import { computed, ref, onMounted, watch,onUnmounted,nextTick  } from 'vue'
import { useRoute } from 'vue-router'
import { useWarehouseStore, type Component } from '../stores/warehouse'
import { useToastStore } from '../stores/toast'

const toast = useToastStore()

const isWipLoading = ref(false)


const searchChipId = ref('')
const searchCassetteId = ref('')




const isLocating = ref(false)           // 查詢 loading 狀態

// 縮放相關
const containerRef = ref<HTMLElement | null>(null)   // canvas-area 的容器
const userScale = ref(1)                             // 使用者額外縮放 (0.5~2 之類)
const autoScale = ref(1)                             // 根據容器大小自動算出來的縮放

// ====== 兩指縮放（pinch）支援 ======
const isPinching = ref(false)
const pinchStartDistance = ref(0)
const pinchStartScale = ref(1)

// 明確宣告：只接受 TouchList，不直接拿 Touch
const getDistance = (touches: TouchList) => {
  // 額外防護：長度不足就回 0
  if (touches.length < 2) return 0
  const t1 = touches[0]!
  const t2 = touches[1]!
  const dx = t2.clientX - t1.clientX
  const dy = t2.clientY - t1.clientY
  return Math.hypot(dx, dy)
}

const handleTouchStart = (e: TouchEvent) => {
  if (e.touches.length === 2) {
    isPinching.value = true
    pinchStartDistance.value = getDistance(e.touches)
    pinchStartScale.value = userScale.value
  }
}

const handleTouchMove = (e: TouchEvent) => {
  if (!isPinching.value || e.touches.length !== 2) return

  e.preventDefault() // 避免瀏覽器自己縮放/捲動

  const newDistance = getDistance(e.touches)
  if (!pinchStartDistance.value) return

  const ratio = newDistance / pinchStartDistance.value
  let nextScale = pinchStartScale.value * ratio

  // 跟滑桿一樣 0.5–2
  nextScale = Math.max(0.5, Math.min(2, nextScale))
  userScale.value = nextScale
}

const handleTouchEnd = (e: TouchEvent) => {
  // 只要少於 2 指就結束 pinch
  if (e.touches.length < 2) {
    isPinching.value = false
    pinchStartDistance.value = 0
  }
}


const handleLocate = async () => {
  const chipId = searchChipId.value.trim()
  const cassetteId = searchCassetteId.value.trim()

  if (!chipId && !cassetteId) {
    toast.info('請至少輸入 Chip ID 或 Cst ID 其中一項')
    return
  }

  try {
    isLocating.value = true

    const res = await store.locateByChipOrCassette({
      chipId,
      cassetteId,
    })

    if (!res || !res.bin_code) {
      toast.error('查無對應儲位')
      return
    }

    if (chipId && res.cassette_id) {
      searchCassetteId.value = res.cassette_id
    }

    const binCode = res.bin_code

    // 高亮儲位
    searchResult.value = binCode
    toast.success(`已找到儲位：${binCode}`)

    setTimeout(() => {
      if (searchResult.value === binCode) {
        searchResult.value = null
      }
    }, 3000)
  } catch (e) {
    console.error(e)
    toast.error('查詢時發生錯誤，請稍後再試')
  } finally {
    isLocating.value = false
  }
}

const route = useRoute()

const store = useWarehouseStore()
const layoutId = route.params.id as string

const isLayoutLoading = ref(false)



// 最終套用在 SVG 上的 scale
const finalScale = computed(() => autoScale.value * userScale.value)
// 先定義 layout（之後 watch 才能用）

const layout = computed(() => store.currentLayout)


// 當 layout 寬高變化時（切換 layout），重新計算
watch(layout, (val) => {
  if (!val) return
  // 等 DOM 更新完再算（避免高度還沒排好）
  nextTick(() => {
    recomputeAutoScale()
  })
})

// 根據容器可用空間重新計算 autoScale
const recomputeAutoScale = () => {
  if (!containerRef.value || !layout.value) return

  const rect = containerRef.value.getBoundingClientRect()

  // 預留一點邊界，避免太貼邊 (例如左右各 16px，上下 16px)
  const paddingX = 32
  const paddingY = 32

  const availableWidth = rect.width - paddingX
  const availableHeight = rect.height - paddingY

  if (availableWidth <= 0 || availableHeight <= 0) return

  const scaleX = availableWidth / layout.value.width
  const scaleY = availableHeight / layout.value.height

  // 取最小值，確保完整塞入
  const s = Math.min(scaleX, scaleY, 1)  // 不超過原始 1 倍（你也可以拿掉這個限制）
  autoScale.value = s > 0 ? s : 1
}



onMounted(async () => {
  try {
    isLayoutLoading.value = true
    await store.fetchLayoutDetails(layoutId)

     recomputeAutoScale()

  window.addEventListener('resize', recomputeAutoScale)
  document.addEventListener('fullscreenchange', recomputeAutoScale)

  } catch (e) {
    console.error(e)
    toast.error('布局載入失敗，請稍後再試')
  } finally {
    isLayoutLoading.value = false
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', recomputeAutoScale)
    document.removeEventListener('fullscreenchange', recomputeAutoScale)
})


const components = computed(() => layout.value?.components || [])
const selectedComp = ref<Component | null>(null)
const wipData = ref<any>(null)

const searchResult = ref<string | null>(null)

// 儲位內 Cassette 數量：key 為 bin code
const binCassetteCounts = ref<Record<string, number>>({})

// 分層用變數
const selectedGroup = ref<any>(null)      // Grade+Model+Stage 分組
const selectedCassette = ref<any>(null)   // Cassette

// 新增：各視圖主層選取
const selectedStage = ref<any>(null)
const selectedModel = ref<any>(null)
const selectedGrade = ref<any>(null)

// 視圖模式：group / cassette / stage / model / grade
type ViewMode = 'group' | 'cassette' | 'stage' | 'model' | 'grade'
const viewMode = ref<ViewMode>('group')

// ---------- 分組表格排序狀態 ----------
type GroupSortKey = 'grade' | 'model' | 'stage' | 'cassetteCount' | 'chipCount'
const groupSortKey = ref<GroupSortKey>('grade')
const groupSortOrder = ref<'asc' | 'desc'>('asc')

const toggleGroupSort = (key: GroupSortKey) => {
  if (groupSortKey.value === key) {
    groupSortOrder.value = groupSortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    groupSortKey.value = key
    groupSortOrder.value = 'asc'
  }
}

const getGroupSortIcon = (key: GroupSortKey) => {
  if (groupSortKey.value !== key) return ''
  return groupSortOrder.value === 'asc' ? '▲' : '▼'
}


const getPolygonPoints = (comp: Component) => {
  if (!comp.shapePoints) return ''
  return comp.shapePoints.map(p => `${p.x},${p.y}`).join(' ')
}

const resetSelections = () => {
  selectedGroup.value = null
  selectedCassette.value = null
  selectedStage.value = null
  selectedModel.value = null
  selectedGrade.value = null
}

const recomputeBinCassetteCounts = () => {
  const result: Record<string, Set<string>> = {}
  if (!wipData.value) {
    binCassetteCounts.value = {}
    return
  }
  // wipData 的結構是：[{ cassette_id, wips: [...] }, ...]
  wipData.value.forEach((cst: any) => {
    const cassetteId = cst.cassette_id
    if (!cassetteId) return
    cst.wips?.forEach((wip: any) => {
      const binCode = wip.bin_code || wip.bin || wip.location || wip.stocker_id || wip.pos_code || wip.pos || ''
      // 如果後端有明確欄位指示儲位 code，可改成正確欄位，例如 wip.bin_id or wip.bin
      // 目前先假設 wip 內有 bin_code 之類，可自行調整
      const key = binCode || ''  // 若你的 API 直接用儲位 code 當 key，這裡改成那個欄位
      if (!key) return
      if (!result[key]) result[key] = new Set<string>()
      result[key].add(cassetteId)
    })
  })

  const countMap: Record<string, number> = {}
  Object.entries(result).forEach(([code, set]) => {
    countMap[code] = set.size
  })
  binCassetteCounts.value = countMap
}

const handleCompClick = async (comp: Component) => {
  selectedComp.value = comp
  searchResult.value = null
  wipData.value = null
  resetSelections()
  viewMode.value = 'group'

  if (!comp.code) {
    binCassetteCounts.value = {}
    return
  }

  try {
    isWipLoading.value = true
    const data = await store.fetchWipData([comp.code])
    wipData.value = data[comp.code] || []
    recomputeBinCassetteCounts()
  } catch (e) {
    console.error(e)
    toast.error(`儲位 ${comp.code} 資料載入失敗`)
  } finally {
    isWipLoading.value = false
  }
}

const closeDetail = () => {
  selectedComp.value = null
  wipData.value = null
  resetSelections()
  binCassetteCounts.value = {}
}

// ----------------------------------------
// 視圖一：分組視圖（Grade / Model / Stage）
// GROUP BY Grade, Model, Stage
// ----------------------------------------
const groupedData = computed(() => {
  if (!wipData.value) return []
  const groups: Record<string, any> = {}
  wipData.value.forEach((cst: any) => {
    cst.wips.forEach((wip: any) => {
      const key = `${wip.grade}__${wip.model_no}__${wip.stage_id}`
      if (!groups[key]) {
        groups[key] = { 
          grade: wip.grade, 
          model: wip.model_no, 
          stage: wip.stage_id, 
          cassettes: new Set<string>(),
          chipCount: 0
        }
      }
      groups[key].cassettes.add(cst.cassette_id)
      groups[key].chipCount += 1
    })
  })
  return Object.values(groups).map((g: any) => ({
    ...g,
    cassetteCount: g.cassettes.size
  }))
})

const sortedGroupedData = computed(() => {
  const data = [...groupedData.value]
  const key = groupSortKey.value
  const order = groupSortOrder.value

  data.sort((a: any, b: any) => {
    const av = a[key]
    const bv = b[key]

    if (key === 'cassetteCount' || key === 'chipCount') {
      const diff = (av as number) - (bv as number)
      return order === 'asc' ? diff : -diff
    }

    const aStr = (av ?? '').toString()
    const bStr = (bv ?? '').toString()
    const cmp = aStr.localeCompare(bStr, 'zh-Hant')
    return order === 'asc' ? cmp : -cmp
  })

  return data
})

// group 視圖：第二層 Cassette
const cassettesInGroup = computed(() => {
  if (!selectedGroup.value || !wipData.value) return []
  const filtered = wipData.value.filter((cst: any) =>
    cst.wips.some((wip: any) =>
      wip.grade === selectedGroup.value.grade &&
      wip.model_no === selectedGroup.value.model &&
      wip.stage_id === selectedGroup.value.stage
    )
  )
  return filtered
})

// ----------------------------------------
// 視圖二：Cassette 視角 (維持二層：Cassette → RAW)
// ----------------------------------------
const cassetteViewList = computed(() => {
  if (!wipData.value) return []
  return wipData.value
    .map((cst: any) => ({
      ...cst,
      chipCount: cst.wips?.length || 0
    }))
    .sort((a: any, b: any) => b.chipCount - a.chipCount)
})

// ----------------------------------------
// 視圖三：Stage 視角
// ----------------------------------------
const stageViewList = computed(() => {
  if (!wipData.value) return []
  const map: Record<string, any> = {}

  wipData.value.forEach((cst: any) => {
    cst.wips.forEach((wip: any) => {
      const key = wip.stage_id || 'UNKNOWN'
      if (!map[key]) {
        map[key] = {
          stage: wip.stage_id,
          totalChips: 0,
          cassettes: new Set<string>(),
          models: new Set<string>(),
          grades: new Set<string>()
        }
      }
      map[key].totalChips += 1
      map[key].cassettes.add(cst.cassette_id)
      map[key].models.add(wip.model_no)
      map[key].grades.add(wip.grade)
    })
  })

  return Object.values(map)
    .map((s: any) => ({
      ...s,
      cassetteCount: s.cassettes.size,
      modelCount: s.models.size,
      gradeCount: s.grades.size
    }))
    .sort((a: any, b: any) => b.totalChips - a.totalChips)
})

// Stage 視圖：第二層 Cassette
const cassettesInStage = computed(() => {
  if (!selectedStage.value || !wipData.value) return []
  const filtered = wipData.value.filter((cst: any) =>
    cst.wips.some((wip: any) => wip.stage_id === selectedStage.value.stage)
  )
  return filtered
})

// ----------------------------------------
// 視圖四：Model 視角
// ----------------------------------------
const modelViewList = computed(() => {
  if (!wipData.value) return []
  const map: Record<string, any> = {}

  wipData.value.forEach((cst: any) => {
    cst.wips.forEach((wip: any) => {
      const key = wip.model_no || 'UNKNOWN'
      if (!map[key]) {
        map[key] = {
          model: wip.model_no,
          totalChips: 0,
          cassettes: new Set<string>(),
          stages: new Set<string>(),
          grades: new Set<string>()
        }
      }
      map[key].totalChips += 1
      map[key].cassettes.add(cst.cassette_id)
      map[key].stages.add(wip.stage_id)
      map[key].grades.add(wip.grade)
    })
  })

  return Object.values(map)
    .map((m: any) => ({
      ...m,
      cassetteCount: m.cassettes.size,
      stageCount: m.stages.size,
      gradeCount: m.grades.size
    }))
    .sort((a: any, b: any) => b.totalChips - a.totalChips)
})

const cassettesInModel = computed(() => {
  if (!selectedModel.value || !wipData.value) return []
  const filtered = wipData.value.filter((cst: any) =>
    cst.wips.some((wip: any) => wip.model_no === selectedModel.value.model)
  )
  return filtered
})

// ----------------------------------------
// 視圖五：Grade 視角
// ----------------------------------------
const gradeViewList = computed(() => {
  if (!wipData.value) return []
  const map: Record<string, any> = {}

  wipData.value.forEach((cst: any) => {
    cst.wips.forEach((wip: any) => {
      const key = wip.grade || 'UNKNOWN'
      if (!map[key]) {
        map[key] = {
          grade: wip.grade,
          totalChips: 0,
          cassettes: new Set<string>(),
          stages: new Set<string>(),
          models: new Set<string>()
        }
      }
      map[key].totalChips += 1
      map[key].cassettes.add(cst.cassette_id)
      map[key].stages.add(wip.stage_id)
      map[key].models.add(wip.model_no)
    })
  })

  return Object.values(map)
    .map((g: any) => ({
      ...g,
      cassetteCount: g.cassettes.size,
      stageCount: g.stages.size,
      modelCount: g.models.size
    }))
    .sort((a: any, b: any) => b.totalChips - a.totalChips)
})

const cassettesInGrade = computed(() => {
  if (!selectedGrade.value || !wipData.value) return []
  const filtered = wipData.value.filter((cst: any) =>
    cst.wips.some((wip: any) => wip.grade === selectedGrade.value.grade)
  )
  return filtered
})

// 總 Cassette (Box) 數：目前先用 binCassetteCounts 的總和
const totalCassetteCount = computed(() => {
  const counts = store.binCassetteCounts || {}
  return Object.values(counts).reduce((sum, n) => sum + (n as number), 0)
})

// 共用：第三層 WIP 詳細 (依目前選的 Cassette)
const wipsInCassette = computed(() => {
  if (!selectedCassette.value) return []
  return selectedCassette.value.wips || []
})

// 畫 bin 顏色：保留你原本的邏輯
const getFillColor = (comp: Component) => {
  if (searchResult.value === comp.code) return 'orange'  // 搜尋結果 bin 改成黃色
  const count = store.binCassetteCounts[comp.code || ''] || 0
  if (count > 29) return 'rgba(239, 68, 68, 0.7)'
  if (count > 0) return 'rgba(16, 185, 129, 0.7)'
  if (comp.props?.color) return comp.props.color
  return 'rgba(30, 41, 59, 0.6)'
}
</script>

<template>
  <div class="operation-container" v-if="layout">
     <div v-if="isLayoutLoading" class="page-loading-overlay">
      <div class="page-loading-box">
        <div class="big-spinner"></div>
        <div class="page-loading-text">布局載入中…</div>
      </div>
    </div>
  <div class="top-bar compact">
  <!-- Layout 標題區 -->
  <div class="title-area">
    <span class="layout-title">{{ layout.name }}</span>
    <span class="layout-summary">
      總 Box：
      <span class="layout-summary-number">{{ totalCassetteCount }}</span>
    </span>
  </div>

  <!-- 縮放控制 -->
  <div class="zoom-control">
    <button @click="userScale = Math.max(0.5, userScale - 0.1)">−</button>
    <input type="range" min="0.5" max="2" step="0.05" v-model.number="userScale"/>
    <button @click="userScale = Math.min(2, userScale + 0.1)">＋</button>
    <span class="zoom-label">{{ Math.round(finalScale * 100) }}%</span>
    <button class="zoom-reset" @click="userScale = 1">重置</button>
  </div>

  <!-- 搜尋功能 -->
  <div class="search-box">
    <input v-model="searchChipId" placeholder="Chip ID..." @keyup.enter="handleLocate"/>
    <input v-model="searchCassetteId" placeholder="Cst ID..." @keyup.enter="handleLocate"/>
    <button @click="handleLocate" :disabled="isLocating">
      <span v-if="!isLocating">查詢儲位</span>
      <span v-else class="btn-loading">查詢中…</span>
    </button>
  </div>
</div>

<main class="canvas-area" ref="containerRef"
  @touchstart.passive="handleTouchStart"
  @touchmove="handleTouchMove"
  @touchend="handleTouchEnd"
  @touchcancel="handleTouchEnd"
>
<div
  class="canvas-viewport"
  :style="{
    width: layout ? `${layout.width}px` : 'auto',  // 這行新增
    transform: `scale(${finalScale})`,
    transformOrigin: 'top left',
     marginLeft: '8px',        // 這樣只會往左多留一點空間
  }"

  >
    <svg
      :viewBox="`0 0 ${layout.width} ${layout.height}`"
      :width="layout.width"
      :height="layout.height"
      preserveAspectRatio="xMidYMid meet"
      style="display: block;"
    >
          <g
            v-for="comp in components"
            :key="comp.id"
            @click="handleCompClick(comp)"
            class="comp-group"
            :class="{ highlighted: searchResult === comp.code }"
          >
            <rect
              v-if="!comp.shapePoints"
              :x="comp.x"
              :y="comp.y"
              :width="comp.width"
              :height="comp.height"
              class="comp-visual"
              :class="comp.type"
              :fill="getFillColor(comp)"
            />
            <g v-else :transform="`translate(${comp.x}, ${comp.y})`">
              <polygon
                :points="getPolygonPoints(comp)"
                class="comp-visual"
                :class="comp.type"
                :fill="getFillColor(comp)"
              />
            </g>

            <!-- 中央顯示儲位名稱 -->
            <text
              v-if="comp.code"
              :x="comp.x + comp.width / 2"
              :y="comp.y + comp.height / 2 + 4"
              fill="white"
              font-size="12"
              text-anchor="middle"
              pointer-events="none"
              class="comp-label"
            >
              {{ comp.code }}
            </text>

            <!-- 中央的機台 / 柱 icon，稍微往下 -->
            <text
              v-if="comp.type === 'machine'"
              :x="comp.x + comp.width/2"
              :y="comp.y + comp.height/2 + 14"
              fill="white"
              font-size="16"
              text-anchor="middle"
              pointer-events="none"
              style="opacity: 0.3"
            >⚙</text>
            <text
              v-if="comp.type === 'pillar'"
              :x="comp.x + comp.width/2"
              :y="comp.y + comp.height/2 + 14"
              fill="white"
              font-size="12"
              text-anchor="middle"
              pointer-events="none"
              style="opacity: 0.3"
            >柱</text>

            <!-- 右上角紅圈：顯示 Cassette 數量 -->
            <g
  v-if="comp.type === 'bin' && store.binCassetteCounts[comp.code || '']"
  class="count-badge"
>
  <circle
    :cx="comp.x + comp.width - 10"
    :cy="comp.y + 10"
    r="10"
    fill="#ef4444"
  />
  <text
    :x="comp.x + comp.width - 10"
    :y="comp.y + 14"
    fill="white"
    font-size="10"
    text-anchor="middle"
    font-weight="bold"
  >
    {{ store.binCassetteCounts[comp.code || ''] }}
  </text>
</g>
          </g>
        </svg>
      </div>
    </main>

   <!-- Detail Panel (Modal) -->
<div v-if="selectedComp" class="detail-overlay" @click.self="closeDetail">
  <div class="detail-card glass-panel">
    <button class="close-btn" @click="closeDetail">×</button>
    <h2>儲位: {{ selectedComp.code }}</h2>

    <!-- WIP loading 狀態顯示 -->
    <div v-if="isWipLoading" class="wip-loading-bar">
      <div class="spinner small"></div>
      <span>資料載入中…</span>
    </div>
  <template v-if="!isWipLoading">
        <!-- 視圖模式切換列 -->
        <div class="view-tabs">
          <button
            class="tab-btn"
            :class="{ active: viewMode === 'group' }"
            @click="viewMode = 'group'; resetSelections()"
          >
            分組視圖 (Grade / Model / Stage)
          </button>
          <button
            class="tab-btn"
            :class="{ active: viewMode === 'cassette' }"
            @click="viewMode = 'cassette'; resetSelections()"
          >
            Box 視圖
          </button>
          <button
            class="tab-btn"
            :class="{ active: viewMode === 'stage' }"
            @click="viewMode = 'stage'; resetSelections()"
          >
            Stage 視圖
          </button>
          <button
            class="tab-btn"
            :class="{ active: viewMode === 'model' }"
            @click="viewMode = 'model'; resetSelections()"
          >
            Model 視圖
          </button>
          <button
            class="tab-btn"
            :class="{ active: viewMode === 'grade' }"
            @click="viewMode = 'grade'; resetSelections()"
          >
            Grade 視圖
          </button>
        </div>

        <!-- 三欄階層容器 -->
        <div class="tier-container">
          <!-- 左欄：主視圖列表 -->
          <div class="tier-column">
            <!-- group -->
            <template v-if="viewMode === 'group'">
              <h3>分組 (Grade / Model / Stage)</h3>
              <div v-if="sortedGroupedData.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th @click="toggleGroupSort('grade')">
                      Grade
                      <span class="sort-icon">{{ getGroupSortIcon('grade') }}</span>
                    </th>
                    <th @click="toggleGroupSort('model')">
                      Model
                      <span class="sort-icon">{{ getGroupSortIcon('model') }}</span>
                    </th>
                    <th @click="toggleGroupSort('stage')">
                      Stage
                      <span class="sort-icon">{{ getGroupSortIcon('stage') }}</span>
                    </th>
                    <th @click="toggleGroupSort('cassetteCount')">
                      Box數
                      <span class="sort-icon">{{ getGroupSortIcon('cassetteCount') }}</span>
                    </th>
                    <th @click="toggleGroupSort('chipCount')">
                      Chips
                      <span class="sort-icon">{{ getGroupSortIcon('chipCount') }}</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="grp in sortedGroupedData"
                    :key="grp.grade + grp.model + grp.stage"
                    @click="selectedGroup = grp; selectedCassette = null"
                    :class="{ active: selectedGroup === grp }"
                  >
                    <td>{{ grp.grade }}</td>
                    <td>{{ grp.model }}</td>
                    <td>{{ grp.stage }}</td>
                    <td>{{ grp.cassetteCount }}</td>
                    <td>{{ grp.chipCount }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <!-- cassette -->
            <template v-else-if="viewMode === 'cassette'">
              <h3>Box 清單 (依 Chip 數量排序)</h3>
              <div v-if="cassetteViewList.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Box ID</th>
                    <th>Chips</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="cst in cassetteViewList"
                    :key="cst.cassette_id"
                    @click="selectedCassette = cst"
                    :class="{ active: selectedCassette === cst }"
                  >
                    <td>{{ cst.cassette_id }}</td>
                    <td>{{ cst.chipCount }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <!-- stage -->
            <template v-else-if="viewMode === 'stage'">
              <h3>Stage 分布</h3>
              <div v-if="stageViewList.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Stage</th>
                    <th>Chips</th>
                    <th>Box數</th>
                    <th>Model數</th>
                    <th>Grade數</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="st in stageViewList"
                    :key="st.stage"
                    @click="selectedStage = st; selectedCassette = null"
                    :class="{ active: selectedStage === st }"
                  >
                    <td>{{ st.stage }}</td>
                    <td>{{ st.totalChips }}</td>
                    <td>{{ st.cassetteCount }}</td>
                    <td>{{ st.modelCount }}</td>
                    <td>{{ st.gradeCount }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <!-- model -->
            <template v-else-if="viewMode === 'model'">
              <h3>Model 分布</h3>
              <div v-if="modelViewList.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Chips</th>
                    <th>Box數</th>
                    <th>Stage數</th>
                    <th>Grade數</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="mdl in modelViewList"
                    :key="mdl.model"
                    @click="selectedModel = mdl; selectedCassette = null"
                    :class="{ active: selectedModel === mdl }"
                  >
                    <td>{{ mdl.model }}</td>
                    <td>{{ mdl.totalChips }}</td>
                    <td>{{ mdl.cassetteCount }}</td>
                    <td>{{ mdl.stageCount }}</td>
                    <td>{{ mdl.gradeCount }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <!-- grade -->
            <template v-else-if="viewMode === 'grade'">
              <h3>Grade 分布</h3>
              <div v-if="gradeViewList.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Grade</th>
                    <th>Chips</th>
                    <th>Box</th>
                    <th>Stage數</th>
                    <th>Model數</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="gr in gradeViewList"
                    :key="gr.grade"
                    @click="selectedGrade = gr; selectedCassette = null"
                    :class="{ active: selectedGrade === gr }"
                  >
                    <td>{{ gr.grade }}</td>
                    <td>{{ gr.totalChips }}</td>
                    <td>{{ gr.cassetteCount }}</td>
                    <td>{{ gr.stageCount }}</td>
                    <td>{{ gr.modelCount }}</td>
                  </tr>
                </tbody>
              </table>
            </template>
          </div>

          <!-- 中欄：第二層 Cassette 清單 -->
          <div class="tier-column">
            <template v-if="viewMode === 'group' && selectedGroup">
              <h3>Box 清單 (該分組底下)</h3>
              <div v-if="cassettesInGroup.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Box ID</th>
                    <th>Chips</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="cst in cassettesInGroup"
                    :key="cst.cassette_id"
                    @click="selectedCassette = cst"
                    :class="{ active: selectedCassette === cst }"
                  >
                    <td>{{ cst.cassette_id }}</td>
                    <td>{{ cst.wips?.length || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <template v-else-if="viewMode === 'stage' && selectedStage">
              <h3>Box 清單 (Stage: {{ selectedStage.stage }})</h3>
              <div v-if="cassettesInStage.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Box ID</th>
                    <th>Chips</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="cst in cassettesInStage"
                    :key="cst.cassette_id"
                    @click="selectedCassette = cst"
                    :class="{ active: selectedCassette === cst }"
                  >
                    <td>{{ cst.cassette_id }}</td>
                    <td>{{ cst.wips?.length || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <template v-else-if="viewMode === 'model' && selectedModel">
              <h3>Box 清單 (Model: {{ selectedModel.model }})</h3>
              <div v-if="cassettesInModel.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Box ID</th>
                    <th>Chips</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="cst in cassettesInModel"
                    :key="cst.cassette_id"
                    @click="selectedCassette = cst"
                    :class="{ active: selectedCassette === cst }"
                  >
                    <td>{{ cst.cassette_id }}</td>
                    <td>{{ cst.wips?.length || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <template v-else-if="viewMode === 'grade' && selectedGrade">
              <h3>Box 清單 (Grade: {{ selectedGrade.grade }})</h3>
              <div v-if="cassettesInGrade.length === 0" class="empty-msg">查無資料</div>
              <table v-else class="side-table">
                <thead>
                  <tr>
                    <th>Box ID</th>
                    <th>Chips</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="cst in cassettesInGrade"
                    :key="cst.cassette_id"
                    @click="selectedCassette = cst"
                    :class="{ active: selectedCassette === cst }"
                  >
                    <td>{{ cst.cassette_id }}</td>
                    <td>{{ cst.wips?.length || 0 }}</td>
                  </tr>
                </tbody>
              </table>
            </template>

            <!-- cassette 視圖（只有兩層）時，中欄顯示提示 -->
            <template v-else-if="viewMode === 'cassette'">
              <h3>第二層</h3>
              <p class="empty-msg">Box 視圖僅提供「Box → RAW」兩層結構。</p>
            </template>

            <template v-else>
              <h3>第二層</h3>
              <p class="empty-msg">請先於左側選擇一個項目。</p>
            </template>
          </div>

          <!-- 右欄：第三層 WIP 詳細 -->
          <div class="tier-column">
            <h3>
              <template v-if="selectedCassette">
                WIP 詳細 (Box: {{ selectedCassette.cassette_id }})
              </template>
              <template v-else>
                WIP 詳細
              </template>
            </h3>

            <template v-if="selectedCassette">
              <table class="wip-table">
                <thead>
                  <tr>
                    <th>Chip ID</th>
                    <th>Grade</th>
                    <th>Model</th>
                    <th>Stage</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="wip in wipsInCassette" :key="wip.sheet_id_chip_id">
                    <td>{{ wip.sheet_id_chip_id }}</td>
                    <td>{{ wip.grade }}</td>
                    <td>{{ wip.model_no }}</td>
                    <td>{{ wip.stage_id }}</td>
                  </tr>
                </tbody>
              </table>
            </template>
            <p v-else class="empty-msg">
              請先在中間的 Box 清單中選擇一個 Box。
            </p>
          </div>
        </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
}

/* ===================== 基本結構 ===================== */
/* 讓最外層就決定是滿視窗高度 */
.operation-container {
  display: flex;
  flex-direction: column;
   height: 100%;      /* 由 layout 決定高度 */
}
/* ===================== Top Bar 區域 ===================== */
.top-bar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(30,41,59,0.5);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

/* 節省高度的 Compact 版本 */
.top-bar.compact {
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
}

.layout-title-block,
.title-area {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.layout-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #e5e7eb;
}
.top-bar.compact .layout-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.layout-summary {
  font-size: 0.95rem;
  color: #9ca3af;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.top-bar.compact .layout-summary {
  font-size: 0.85rem;
}

.layout-summary-number {
  min-width: 48px;
  padding: 0.15rem 0.7rem;
  border-radius: 999px;
  text-align: center;
  background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(56,189,248,0.3));
  border: 1px solid rgba(96,165,250,0.8);
  color: #e5f2ff;
  font-weight: 700;
  font-size: 1rem;
  box-shadow: 0 0 10px rgba(59,130,246,0.6);
}
.top-bar.compact .layout-summary-number {
  min-width: 40px;
  padding: 0.1rem 0.5rem;
  font-size: 0.85rem;
}

.top-bar-controls {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

/* ===================== 縮放控制 ===================== */
.zoom-control {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: #e5e7eb;
}
.top-bar.compact .zoom-control {
  font-size: 0.75rem;
}

.zoom-btn {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  border: 1px solid rgba(148,163,184,0.8);
  background: rgba(15,23,42,0.9);
  color: #e5e7eb;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.zoom-btn:hover {
  background: rgba(37,99,235,0.8);
}

.zoom-label {
  min-width: 52px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: #cbd5f5;
}

.zoom-control input[type="range"] {
  width: 140px;
  appearance: none;
  height: 4px;
  border-radius: 999px;
  background: rgba(148,163,184,0.4);
  outline: none;
}
.top-bar.compact .zoom-control input[type="range"] {
  width: 100px;
}
.zoom-control input[type="range"]::-webkit-slider-thumb,
.zoom-control input[type="range"]::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: #3b82f6;
  box-shadow: 0 0 6px rgba(59,130,246,0.8);
  cursor: pointer;
}

/* ===================== 搜尋框 ===================== */
.search-box {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
}
.top-bar.compact .search-box {
  gap: 0.35rem;
}
.search-box input {
  width: 180px;
  padding: 0.5rem;
  border-radius: 4px;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
}
.top-bar.compact .search-box input {
  width: 130px;
  padding: 0.3rem;
  font-size: 0.8rem;
}
.search-box button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  background: #3b82f6;
  color: white;
  border: none;
  cursor: pointer;
}
.top-bar.compact .search-box button {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
}
.search-box button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* ===================== 畫布 ===================== */
.canvas-area {
  flex: 1;
  width: 100%;
  /* 不再指定 height: 100% */
  background: #0f172a;
  display: block;
  justify-content: center;
  
  overflow: auto;
  padding: 1rem 0;
}
.canvas-viewport {
  position: relative;
  box-shadow: 0 0 30px rgba(0,0,0,0.5);
  background: rgba(255,255,255,0.02);
  margin: 0 auto;
}
.comp-visual {
  stroke: rgba(255,255,255,0.3);
  stroke-width: 1;
  cursor: pointer;
  transition: all 0.2s;
}
.comp-visual:hover {
  stroke: #60a5fa;
  stroke-width: 2;
  filter: brightness(1.2);
}
.highlighted .comp-visual {
  stroke: #fbbf24;
  stroke-width: 3;
  filter: drop-shadow(0 0 10px #fbbf24);
}
.comp-label {
  text-shadow: 1px 1px 2px black;
}

/* ===================== Detail Panel ===================== */
.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}
.detail-card {
  width: 1200px;
  max-height: 80vh;
  overflow-y: auto;
  background: #1e293b;
  padding: 1rem;
  border-radius: 12px;
  position: relative;
  color: white;
}
.close-btn {
  position: absolute;
  right: 1rem;
  top: 1rem;
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
}

/* 視圖切換 tabs */
.view-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.5rem 0 1rem;
}
.tab-btn {
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  border: 1px solid rgba(148,163,184,0.8);
  background: rgba(15,23,42,0.8);
  color: #e5e7eb;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.tab-btn:hover {
  background: rgba(30,64,175,0.6);
}
.tab-btn.active {
  background: #3b82f6;
  border-color: #60a5fa;
  color: white;
}

/* ===================== 三欄表格 ===================== */
.tier-container {
  display: flex;
  gap: 1rem;
}
.tier-column {
  flex: 1;
  background: rgba(255,255,255,0.05);
  padding: 0.5rem;
  border-radius: 6px;
  overflow-y: auto;
  max-height: 60vh;
}
.tier-column h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: #fbbf24;
}
.side-table,
.wip-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.side-table th, .wip-table th {
  text-align: left;
  color: #94a3b8;
  border-bottom: 1px solid #475569;
  padding: 0.3rem;
}
.side-table td, .wip-table td {
  padding: 0.3rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.side-table tr {
  cursor: pointer;
}
.side-table tr:hover {
  background: rgba(255,255,255,0.08);
}
.side-table tr.active {
  background: rgba(59,130,246,0.3);
}
.sort-icon {
  margin-left: 3px;
  font-size: 0.7rem;
  color: #e5e7eb;
}

/* ===================== Loading 與其他小元件 ===================== */
.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.spinner {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #ffffff;
  animation: spin 0.8s linear infinite;
}
.spinner.small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(148,163,184,0.5);
  border-top-color: #3b82f6;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.empty-msg {
  color: #9ca3af;
  font-size: 0.9rem;
  line-height: 1.4;
}
.page-loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15,23,42,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.page-loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 2rem;
  border-radius: 12px;
  background: rgba(15,23,42,0.9);
  box-shadow: 0 10px 30px rgba(0,0,0,0.6);
  border: 1px solid rgba(148,163,184,0.4);
}
.big-spinner {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 3px solid rgba(148,163,184,0.5);
  border-top-color: #3b82f6;
  animation: spin 0.8s linear infinite;
}
.page-loading-text {
  color: #e5e7eb;
  font-size: 0.95rem;
}
.wip-loading-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  margin-bottom: 0.75rem;
  border-radius: 6px;
  background: rgba(15,23,42,0.8);
  color: #e5e7eb;
  font-size: 0.85rem;
}

:fullscreen .canvas-area {
  height: 100%;
  width:100%
}
</style>
