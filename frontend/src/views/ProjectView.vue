<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useBoardStore } from '../stores/board'
import { useActivitiesStore } from '../stores/activities'

const boardStore = useBoardStore()
const activitiesStore = useActivitiesStore()

const viewMode = ref<'gantt' | 'node'>('gantt')
const detailLevel = ref<'operational' | 'high'>('operational')
const newActivityName = ref('')
const newActivityDuration = ref(1)
const newActivityParent = ref<number | null>(null)
const newDepPredecessor = ref<number | null>(null)
const newDepSuccessor = ref<number | null>(null)
const decisionLabel = ref('')
const decisionRationale = ref('')
const actionError = ref('')

onMounted(async () => {
  await boardStore.fetchBoard()
  if (boardStore.board) {
    await activitiesStore.fetchAll(boardStore.board.id)
  }
})

// Only top-level activities (no parent themselves) are valid parent
// choices — mirrors the one-level-only backend rule directly in the UI.
const availableParents = computed(() => activitiesStore.activities.filter((a) => a.parent === null))

async function handleAddActivity() {
  if (!newActivityName.value.trim() || !boardStore.board) return
  await activitiesStore.createActivity(
    boardStore.board.id,
    newActivityName.value,
    newActivityDuration.value,
    newActivityParent.value
  )
  newActivityName.value = ''
  newActivityDuration.value = 1
  newActivityParent.value = null
}

async function handleAddDependency() {
  if (!newDepPredecessor.value || !newDepSuccessor.value) return
  actionError.value = ''
  try {
    await activitiesStore.createDependency(newDepPredecessor.value, newDepSuccessor.value)
    newDepPredecessor.value = null
    newDepSuccessor.value = null
  } catch (err: any) {
    actionError.value = err?.response?.data?.non_field_errors?.[0] ?? 'Could not add dependency.'
  }
}

async function handleCreateDecisionNode() {
  if (!decisionRationale.value.trim() || !boardStore.board) return
  actionError.value = ''
  try {
    await activitiesStore.createDecisionNode(
      boardStore.board.id,
      decisionLabel.value || 'Baseline',
      decisionRationale.value
    )
    decisionLabel.value = ''
    decisionRationale.value = ''
  } catch (err: any) {
    actionError.value = err?.response?.data?.detail ?? 'Could not recalculate — check for a dependency cycle.'
  }
}

// Which activities actually render at the current detail level:
// operational = every leaf activity (children AND top-level activities
// with no children); high = only top-level activities, with children
// collapsed into their parent's rolled-up bar/node.
// Operational level: only genuine leaf activities — a container/parent
// (one that has children) is never itself real work, so it must never
// appear as if it were a card/row alongside its own children.
// High level: only top-level activities (parent === null) — children
// collapse into their parent's rolled-up bar/node.
const visibleActivities = computed(() => {
  if (detailLevel.value === 'operational') {
    return activitiesStore.activities.filter((a) => activitiesStore.childrenOf(a.id).length === 0)
  }
  return activitiesStore.activities.filter((a) => a.parent === null)
})

const DAY_WIDTH = 30
function scheduleForDisplay(activityId: number) {
  if (detailLevel.value === 'high') {
    return activitiesStore.rollupFor(activityId)
  }
  return activitiesStore.scheduleFor(activityId)
}
function barStyle(activityId: number) {
  const s = scheduleForDisplay(activityId)
  if (!s) return {}
  return {
    marginLeft: `${s.early_start * DAY_WIDTH}px`,
    width: `${(s.early_finish - s.early_start) * DAY_WIDTH}px`,
  }
}
function isCritical(activityId: number) {
  return scheduleForDisplay(activityId)?.float === 0
}
function barLabel(activityId: number) {
  const s = scheduleForDisplay(activityId)
  if (!s) return ''
  return `${s.early_finish - s.early_start}d`
}

// Node view layout — operates on visibleActivities and, at the high
// level, promotedDependencies (cross-group edges only).
const displayDependencies = computed(() =>
  detailLevel.value === 'high' ? activitiesStore.promotedDependencies() : activitiesStore.dependencies
)

const nodeLevels = computed(() => {
  const level: Record<number, number> = {}
  const activityIds = visibleActivities.value.map((a) => a.id)
  const predecessorsOf: Record<number, number[]> = {}
  activityIds.forEach((id) => (predecessorsOf[id] = []))
  displayDependencies.value.forEach((d) => {
    if (predecessorsOf[d.successor]) predecessorsOf[d.successor].push(d.predecessor)
  })

  function levelOf(id: number, seen = new Set<number>()): number {
    if (level[id] !== undefined) return level[id]
    if (seen.has(id)) return 0
    seen.add(id)
    const preds = predecessorsOf[id] || []
    const lvl = preds.length === 0 ? 0 : Math.max(...preds.map((p) => levelOf(p, seen))) + 1
    level[id] = lvl
    return lvl
  }

  activityIds.forEach((id) => levelOf(id))
  return level
})

const nodePositions = computed(() => {
  const positions: Record<number, { x: number; y: number }> = {}
  const countPerLevel: Record<number, number> = {}
  const COL_WIDTH = 160
  const ROW_HEIGHT = 90
  visibleActivities.value.forEach((a) => {
    const lvl = nodeLevels.value[a.id] ?? 0
    const row = countPerLevel[lvl] ?? 0
    countPerLevel[lvl] = row + 1
    positions[a.id] = { x: lvl * COL_WIDTH + 20, y: row * ROW_HEIGHT + 20 }
  })
  return positions
})

function activityName(id: number) {
  return activitiesStore.activities.find((a) => a.id === id)?.name ?? '?'
}
</script>

<template>
  <div class="p-6">
    <h1 class="text-2xl font-semibold text-gray-900 mb-4">Project Schedule</h1>

    <div v-if="actionError" class="text-red-600 bg-red-50 p-3 rounded mb-4">
      {{ actionError }}
    </div>

    <div class="grid grid-cols-2 gap-4 mb-6">
      <form @submit.prevent="handleAddActivity" class="bg-white p-4 rounded-lg shadow space-y-2">
        <h2 class="font-medium text-gray-700">Add activity</h2>
        <input v-model="newActivityName" type="text" placeholder="Activity name" required
          class="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
        <input v-model.number="newActivityDuration" type="number" min="1" placeholder="Duration (days)"
          class="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
        <select v-model="newActivityParent" class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
          <option :value="null">No parent (top-level)</option>
          <option v-for="a in availableParents" :key="a.id" :value="a.id">Under: {{ a.name }}</option>
        </select>
        <button type="submit" class="bg-indigo-600 text-white px-3 py-1 rounded text-sm">Add</button>
      </form>

      <form @submit.prevent="handleAddDependency" class="bg-white p-4 rounded-lg shadow space-y-2">
        <h2 class="font-medium text-gray-700">Add dependency</h2>
        <select v-model="newDepPredecessor" class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
          <option :value="null">Predecessor…</option>
          <option v-for="a in activitiesStore.activities" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
        <select v-model="newDepSuccessor" class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
          <option :value="null">Successor…</option>
          <option v-for="a in activitiesStore.activities" :key="a.id" :value="a.id">{{ a.name }}</option>
        </select>
        <button type="submit" class="bg-indigo-600 text-white px-3 py-1 rounded text-sm">Add</button>
      </form>
    </div>

    <form @submit.prevent="handleCreateDecisionNode" class="bg-white p-4 rounded-lg shadow mb-6 space-y-2">
      <h2 class="font-medium text-gray-700">
        Decision Node
        <span class="text-xs text-gray-400 font-normal" title="Recalculating creates a new baseline — the prior one is kept, not overwritten. This is the only way the schedule changes.">
          (recalculate &amp; create new baseline)
        </span>
      </h2>
      <input v-model="decisionLabel" type="text" placeholder="Baseline label (optional)"
        class="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
      <textarea v-model="decisionRationale" placeholder="Rationale — why recalculate now?" required
        class="w-full border border-gray-300 rounded px-2 py-1 text-sm" rows="2" />
      <button type="submit" class="bg-indigo-600 text-white px-4 py-1.5 rounded text-sm">
        Recalculate &amp; Create Baseline
      </button>
      <p v-if="activitiesStore.activeBaseline" class="text-xs text-gray-500">
        Active baseline: <strong>{{ activitiesStore.activeBaseline.label }}</strong>
      </p>
    </form>


    <div class="flex gap-4 mb-4">
      <div class="flex gap-2">
        <button @click="viewMode = 'gantt'" :class="viewMode === 'gantt' ? 'bg-indigo-600 text-white' : 'bg-gray-200'"
          class="px-3 py-1 rounded text-sm">Gantt</button>
        <button @click="viewMode = 'node'" :class="viewMode === 'node' ? 'bg-indigo-600 text-white' : 'bg-gray-200'"
          class="px-3 py-1 rounded text-sm">Node diagram</button>
      </div>
      <div class="flex gap-2 border-l pl-4">
        <button @click="detailLevel = 'high'" :class="detailLevel === 'high' ? 'bg-indigo-600 text-white' : 'bg-gray-200'"
          class="px-3 py-1 rounded text-sm">High level</button>
        <button @click="detailLevel = 'operational'" :class="detailLevel === 'operational' ? 'bg-indigo-600 text-white' : 'bg-gray-200'"
          class="px-3 py-1 rounded text-sm">Operational level</button>
      </div>
    </div>

    <div v-if="!activitiesStore.activeBaseline" class="text-gray-500 text-sm">
      No baseline yet — add activities and dependencies, then trigger a Decision Node to compute the schedule.
    </div>

    <div v-else-if="viewMode === 'gantt'" class="bg-white rounded-lg shadow p-4 space-y-2">
      <div v-for="a in visibleActivities" :key="a.id" class="flex items-center gap-2">
        <div class="w-32 text-sm text-gray-700 truncate">{{ a.name }}</div>
        <div
          :style="barStyle(a.id)"
          :class="isCritical(a.id) ? 'bg-red-400' : 'bg-indigo-300'"
          class="h-6 rounded text-white text-xs flex items-center px-1"
          :title="isCritical(a.id) ? 'On critical path (zero float)' : 'Has float'"
        >
          {{ barLabel(a.id) }}
        </div>
      </div>
    </div>

    <div v-else class="bg-white rounded-lg shadow p-4 overflow-auto">
      <svg :width="900" :height="400">
        <line
          v-for="(dep, i) in displayDependencies"
          :key="i"
          :x1="(nodePositions[dep.predecessor]?.x ?? 0) + 130"
          :y1="(nodePositions[dep.predecessor]?.y ?? 0) + 20"
          :x2="nodePositions[dep.successor]?.x ?? 0"
          :y2="(nodePositions[dep.successor]?.y ?? 0) + 20"
          stroke="#9ca3af"
          stroke-width="2"
          marker-end="url(#arrow)"
        />
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" fill="#9ca3af" />
          </marker>
        </defs>
        <g v-for="a in visibleActivities" :key="a.id">
          <rect
            :x="nodePositions[a.id]?.x ?? 0"
            :y="nodePositions[a.id]?.y ?? 0"
            width="130"
            height="40"
            rx="6"
            :fill="isCritical(a.id) ? '#f87171' : '#e0e7ff'"
            stroke="#6366f1"
          />
          <text
            :x="(nodePositions[a.id]?.x ?? 0) + 65"
            :y="(nodePositions[a.id]?.y ?? 0) + 24"
            text-anchor="middle"
            font-size="12"
          >
            {{ a.name }} ({{ barLabel(a.id) }})
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>