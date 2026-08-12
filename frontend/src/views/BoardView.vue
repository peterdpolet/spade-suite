<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useBoardStore } from '../stores/board'
import { useIssuesStore } from '../stores/issues'
import { useTeamsStore } from '../stores/teams'
import { useLabelsStore } from '../stores/labels'
import type { Issue } from '../stores/issues'
import IssueForm from '../components/IssueForm.vue'

const boardStore = useBoardStore()
const issuesStore = useIssuesStore()
const teamsStore = useTeamsStore()
const labelsStore = useLabelsStore()

const openFormStatusId = ref<number | null>(null)
const editingIssue = ref<Issue | null>(null)
const actionError = ref('')
const searchText = ref('')
const labelFilter = ref<number | null>(null)
const draggedIssueId = ref<number | null>(null)
let socket: WebSocket | null = null

const PRIORITY_TIERS: Issue['priority'][] = ['high', 'medium', 'low']

async function reloadIssues() {
  if (!boardStore.board) return
  await issuesStore.fetchIssues(boardStore.board.id, {
    search: searchText.value || undefined,
    label: labelFilter.value ?? undefined,
  })
}

watch([searchText, labelFilter], reloadIssues)

// PLANTED BUG (Module 10, deliberate — see
// Spadework_Tier2_Kanban_Spec_v1.md "Planted teaching bugs"): naive
// auto-reconnect. On disconnect, we reconnect after a short delay —
// but we do NOT refetch board state on reconnect. Any events broadcast
// to this board WHILE disconnected are simply lost forever. The
// socket comes back up, looks connected, and silently shows stale
// data mixed with whatever arrives live from that point on — no error,
// no obvious sign anything's wrong. That's the actual "reconnect
// desync" bug: not that reconnect fails, but that it succeeds while
// silently skipping the gap.
function connectSocket(boardId: number) {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  socket = new WebSocket(`${protocol}://${location.host}/ws/board/${boardId}/`)
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    issuesStore.applyRealtimeEvent(data.event, data.issue)
  }
  socket.onerror = () => {
    actionError.value = 'Live updates disconnected — changes made elsewhere may not appear until you refresh.'
  }
  socket.onclose = () => {
    setTimeout(() => connectSocket(boardId), 2000)
  }
}

onMounted(async () => {
  await boardStore.fetchBoard()
  if (boardStore.board) {
    await issuesStore.fetchIssues(boardStore.board.id)
    await labelsStore.fetchLabels(boardStore.board.id)
    connectSocket(boardStore.board.id)
  }
  await teamsStore.fetchTeams()
})

onUnmounted(() => {
  socket?.close()
})

const todoStatusId = computed(
  () => boardStore.board?.statuses.find((s) => s.name === 'Todo')?.id
)

function sortedList(statusId: number, priority?: Issue['priority']) {
  return issuesStore.issues
    .filter((i) => i.status === statusId && (!priority || i.priority === priority))
    .sort((a, b) => a.order.localeCompare(b.order))
}

function openAddForm(statusId: number) {
  editingIssue.value = null
  openFormStatusId.value = statusId
}

function openEditForm(issue: Issue) {
  openFormStatusId.value = null
  editingIssue.value = issue
}

async function handleSave(payload: Partial<Issue>) {
  actionError.value = ''
  try {
    if (editingIssue.value) {
      await issuesStore.updateIssue(editingIssue.value.id, payload)
      editingIssue.value = null
    } else {
      await issuesStore.createIssue(payload)
      openFormStatusId.value = null
    }
  } catch {
    actionError.value = 'Could not save issue — check the fields and try again.'
  }
}

function handleCancel() {
  openFormStatusId.value = null
  editingIssue.value = null
}

function handleDragStart(issue: Issue) {
  draggedIssueId.value = issue.id
}

async function maybeUpdatePriority(priority?: Issue['priority']) {
  if (!priority || !draggedIssueId.value) return
  const dragged = issuesStore.issues.find((i) => i.id === draggedIssueId.value)
  if (dragged && dragged.priority !== priority) {
    await issuesStore.updateIssue(draggedIssueId.value, { priority })
  }
}

async function handleDropOnCard(statusId: number, targetIssue: Issue, priority?: Issue['priority']) {
  if (!draggedIssueId.value || draggedIssueId.value === targetIssue.id) return
  const list = sortedList(statusId, priority).filter((i) => i.id !== draggedIssueId.value)
  const idx = list.findIndex((i) => i.id === targetIssue.id)
  const before = idx > 0 ? list[idx - 1] : undefined
  await maybeUpdatePriority(priority)
  await issuesStore.reorderIssue(draggedIssueId.value, statusId, before?.id, targetIssue.id)
  draggedIssueId.value = null
}

async function handleDropAtEnd(statusId: number, priority?: Issue['priority']) {
  if (!draggedIssueId.value) return
  const list = sortedList(statusId, priority).filter((i) => i.id !== draggedIssueId.value)
  const before = list.length ? list[list.length - 1] : undefined
  await maybeUpdatePriority(priority)
  await issuesStore.reorderIssue(draggedIssueId.value, statusId, before?.id, undefined)
  draggedIssueId.value = null
}
</script>

<template>
  <div class="p-6">
    <div v-if="actionError" class="text-red-600 bg-red-50 p-3 rounded mb-4">
      {{ actionError }}
    </div>

    <div v-if="boardStore.loading || issuesStore.loading" class="text-gray-500">
      Loading board…
    </div>
    <div v-else-if="boardStore.error" class="text-red-600 bg-red-50 p-3 rounded">
      {{ boardStore.error }}
    </div>

    <div v-else-if="boardStore.board">
      <h1 class="text-2xl font-semibold text-gray-900 mb-1">{{ boardStore.board.name }}</h1>
      <p class="text-gray-500 text-sm mb-4">{{ boardStore.board.description }}</p>

      <div class="flex gap-2 mb-6">
        <input
          v-model="searchText"
          type="text"
          placeholder="Search by title…"
          class="border border-gray-300 rounded px-3 py-1.5 text-sm w-64"
        />
        <select v-model="labelFilter" class="border border-gray-300 rounded px-3 py-1.5 text-sm">
          <option :value="null">All labels</option>
          <option v-for="l in labelsStore.labels" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
      </div>

      <div class="grid grid-cols-4 gap-4">
        <div
          v-for="status in boardStore.board.statuses"
          :key="status.id"
          class="bg-gray-100 rounded-lg p-3 min-h-[400px]"
          @dragover.prevent
          @drop="status.id !== todoStatusId && handleDropAtEnd(status.id)"
        >
          <div class="flex items-center justify-between mb-2">
            <h2 class="font-medium text-gray-700">{{ status.name }}</h2>
            <button
              @click="openAddForm(status.id)"
              class="text-indigo-600 text-sm hover:underline"
            >
              + Add
            </button>
          </div>

          <IssueForm
            v-if="openFormStatusId === status.id"
            :board-id="boardStore.board.id"
            :status-id="status.id"
            :status-name="status.name"
            class="mb-2"
            @save="handleSave"
            @cancel="handleCancel"
          />

          <template v-if="status.id === todoStatusId">
            <div v-for="tier in PRIORITY_TIERS" :key="tier" class="mb-3">
              <div class="text-xs font-medium text-gray-500 uppercase mb-1">{{ tier }}</div>
              <div
                class="space-y-2 min-h-[40px]"
                @dragover.prevent
                @drop="handleDropAtEnd(status.id, tier)"
              >
                <template v-for="issue in sortedList(status.id, tier)" :key="issue.id">
                  <IssueForm
                    v-if="editingIssue?.id === issue.id"
                    :board-id="boardStore.board.id"
                    :status-id="status.id"
                    :status-name="status.name"
                    :issue="issue"
                    @save="handleSave"
                    @cancel="handleCancel"
                  />
                  <div
                    v-else
                    draggable="true"
                    @dragstart="handleDragStart(issue)"
                    @dragover.prevent
                    @drop.stop="handleDropOnCard(status.id, issue, tier)"
                    @click="openEditForm(issue)"
                    class="bg-white p-3 rounded shadow text-sm cursor-move hover:shadow-md"
                  >
                    <div class="font-medium text-gray-900">{{ issue.title }}</div>
                    <div class="text-xs text-gray-500 mt-1">
                      <span v-if="issue.assignee">assigned</span>
                    </div>
                    <div v-if="issue.labels.length" class="flex gap-1 mt-1 flex-wrap">
                      <span
                        v-for="l in issue.labels"
                        :key="l.id"
                        class="bg-indigo-100 text-indigo-700 text-xs px-1.5 py-0.5 rounded"
                      >
                        {{ l.name }}
                      </span>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </template>

          <div v-else class="space-y-2">
            <template v-for="issue in sortedList(status.id)" :key="issue.id">
              <IssueForm
                v-if="editingIssue?.id === issue.id"
                :board-id="boardStore.board.id"
                :status-id="status.id"
                :status-name="status.name"
                :issue="issue"
                @save="handleSave"
                @cancel="handleCancel"
              />
              <div
                v-else
                draggable="true"
                @dragstart="handleDragStart(issue)"
                @dragover.prevent
                @drop.stop="handleDropOnCard(status.id, issue)"
                @click="openEditForm(issue)"
                class="bg-white p-3 rounded shadow text-sm cursor-move hover:shadow-md"
              >
                <div class="font-medium text-gray-900">{{ issue.title }}</div>
                <div class="text-xs text-gray-500 mt-1">
                  {{ issue.priority }}
                  <span v-if="issue.assignee"> · assigned</span>
                </div>
                <div v-if="issue.labels.length" class="flex gap-1 mt-1 flex-wrap">
                  <span
                    v-for="l in issue.labels"
                    :key="l.id"
                    class="bg-indigo-100 text-indigo-700 text-xs px-1.5 py-0.5 rounded"
                  >
                    {{ l.name }}
                  </span>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
