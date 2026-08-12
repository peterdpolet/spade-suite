<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useTeamsStore } from '../stores/teams'
import { useCommentsStore } from '../stores/comments'
import { useLabelsStore } from '../stores/labels'
import type { Issue } from '../stores/issues'

const props = defineProps<{
  boardId: number
  statusId: number
  statusName: string
  issue?: Issue | null
}>()

const emit = defineEmits<{
  save: [payload: Partial<Issue>]
  cancel: []
}>()

const teamsStore = useTeamsStore()
const commentsStore = useCommentsStore()
const labelsStore = useLabelsStore()

const title = ref(props.issue?.title ?? '')
const description = ref(props.issue?.description ?? '')
const priority = ref<Issue['priority']>(props.issue?.priority ?? 'medium')
const team = ref<number | null>(props.issue?.team ?? null)
const assignee = ref<number | null>(props.issue?.assignee ?? null)
const targetDate = ref(props.issue?.target_completion_date ?? '')
const newComment = ref('')
const selectedLabelToAdd = ref<number | null>(null)
// Local copy so the label chip list updates immediately without
// waiting on a full issue refetch from the parent.
const currentLabels = ref(props.issue?.labels ?? [])

const availableMembers = computed(() => {
  const selectedTeam = teamsStore.teams.find((t) => t.id === team.value)
  return selectedTeam?.memberships ?? []
})

const issueComments = computed(() => {
  if (!props.issue?.id) return []
  return commentsStore.commentsByIssue[props.issue.id] ?? []
})

// Labels not already attached to this issue — no point offering a
// duplicate in the dropdown.
const availableLabelsToAdd = computed(() => {
  const attachedIds = new Set(currentLabels.value.map((l) => l.id))
  return labelsStore.labels.filter((l) => !attachedIds.has(l.id))
})

watch(team, () => {
  if (assignee.value && !availableMembers.value.some((m) => m.user === assignee.value)) {
    assignee.value = null
  }
})

onMounted(() => {
  if (props.issue?.id) {
    commentsStore.fetchComments(props.issue.id)
  }
})

async function handleAddComment() {
  if (!newComment.value.trim() || !props.issue?.id) return
  await commentsStore.postComment(props.issue.id, newComment.value)
  newComment.value = ''
}

async function handleAddLabel() {
  if (!selectedLabelToAdd.value || !props.issue?.id) return
  const label = labelsStore.labels.find((l) => l.id === selectedLabelToAdd.value)
  if (!label) return
  await labelsStore.addLabelToIssue(props.issue.id, label.id)
  currentLabels.value.push(label)
  selectedLabelToAdd.value = null
}

async function handleRemoveLabel(labelId: number) {
  if (!props.issue?.id) return
  await labelsStore.removeLabelFromIssue(props.issue.id, labelId)
  currentLabels.value = currentLabels.value.filter((l) => l.id !== labelId)
}

function handleSubmit() {
  emit('save', {
    board: props.boardId,
    status: props.statusId,
    title: title.value,
    description: description.value,
    priority: priority.value,
    team: team.value,
    assignee: assignee.value,
    target_completion_date: targetDate.value || null,
  })
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="bg-white p-3 rounded shadow space-y-2 text-sm">
    <input
      v-model="title"
      type="text"
      placeholder="Issue title"
      required
      class="w-full border border-gray-300 rounded px-2 py-1"
    />
    <textarea
      v-model="description"
      placeholder="Description (optional)"
      rows="2"
      class="w-full border border-gray-300 rounded px-2 py-1"
    />
    <select v-model="priority" class="w-full border border-gray-300 rounded px-2 py-1">
      <option value="low">Low</option>
      <option value="medium">Medium</option>
      <option value="high">High</option>
    </select>
    <select v-model="team" class="w-full border border-gray-300 rounded px-2 py-1">
      <option :value="null">No team</option>
      <option v-for="t in teamsStore.teams" :key="t.id" :value="t.id">{{ t.name }}</option>
    </select>
    <select
      v-model="assignee"
      :disabled="!team"
      class="w-full border border-gray-300 rounded px-2 py-1 disabled:bg-gray-100"
    >
      <option :value="null">Unassigned</option>
      <option v-for="m in availableMembers" :key="m.user" :value="m.user">{{ m.username }}</option>
    </select>
    <input
      v-model="targetDate"
      type="date"
      class="w-full border border-gray-300 rounded px-2 py-1"
    />
    <div class="flex gap-2">
      <button type="submit" class="bg-indigo-600 text-white px-3 py-1 rounded text-xs">
        Save
      </button>
      <button type="button" @click="emit('cancel')" class="bg-gray-200 px-3 py-1 rounded text-xs">
        Cancel
      </button>
    </div>

    <div v-if="issue?.id" class="pt-2 border-t border-gray-200 mt-2">
      <div class="text-xs font-medium text-gray-500 mb-1">Labels</div>
      <div class="flex gap-1 flex-wrap mb-2">
        <span
          v-for="l in currentLabels"
          :key="l.id"
          class="bg-indigo-100 text-indigo-700 text-xs px-1.5 py-0.5 rounded flex items-center gap-1"
        >
          {{ l.name }}
          <button type="button" @click="handleRemoveLabel(l.id)" class="text-indigo-400 hover:text-indigo-700">×</button>
        </span>
      </div>
      <div class="flex gap-1">
        <select v-model="selectedLabelToAdd" class="flex-1 border border-gray-300 rounded px-2 py-1 text-xs">
          <option :value="null">Add a label…</option>
          <option v-for="l in availableLabelsToAdd" :key="l.id" :value="l.id">{{ l.name }}</option>
        </select>
        <button type="button" @click="handleAddLabel" class="bg-gray-200 px-2 py-1 rounded text-xs">
          Add
        </button>
      </div>
    </div>

    <div v-if="issue?.id" class="pt-2 border-t border-gray-200 mt-2">
      <div class="text-xs font-medium text-gray-500 mb-1">Comments</div>
      <div class="space-y-1 mb-2 max-h-32 overflow-y-auto">
        <div v-for="c in issueComments" :key="c.id" class="text-xs">
          <span class="font-medium">{{ c.author_username }}:</span> {{ c.body }}
        </div>
        <div v-if="issueComments.length === 0" class="text-gray-400 text-xs">
          No comments yet.
        </div>
      </div>
      <div class="flex gap-1">
        <input
          v-model="newComment"
          type="text"
          placeholder="Add a comment…"
          class="flex-1 border border-gray-300 rounded px-2 py-1 text-xs"
        />
        <button
          type="button"
          @click="handleAddComment"
          class="bg-gray-200 px-2 py-1 rounded text-xs"
        >
          Post
        </button>
      </div>
    </div>
  </form>
</template>
