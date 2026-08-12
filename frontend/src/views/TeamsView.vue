<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTeamsStore } from '../stores/teams'

const teamsStore = useTeamsStore()

const newTeamName = ref('')
const newTeamDescription = ref('')
const newMemberUserId = ref<Record<number, string>>({})
const actionError = ref('')

onMounted(() => {
  teamsStore.fetchTeams()
})

async function handleCreateTeam() {
  if (!newTeamName.value.trim()) return
  actionError.value = ''
  try {
    await teamsStore.createTeam(newTeamName.value, newTeamDescription.value)
    newTeamName.value = ''
    newTeamDescription.value = ''
  } catch {
    actionError.value = 'Could not create team.'
  }
}

async function handleAddMember(teamId: number) {
  const userId = Number(newMemberUserId.value[teamId])
  if (!userId) return
  actionError.value = ''
  try {
    await teamsStore.addMember(teamId, userId)
    newMemberUserId.value[teamId] = ''
  } catch (err: any) {
    actionError.value = err?.response?.data?.detail ?? 'Could not add member.'
  }
}

async function handleRemoveMember(teamId: number, userId: number) {
  try {
    await teamsStore.removeMember(teamId, userId)
  } catch {
    actionError.value = 'Could not remove member.'
  }
}
</script>

<template>
  <div class="p-6 max-w-3xl">
    <h1 class="text-2xl font-semibold text-gray-900 mb-6">Teams</h1>

    <div v-if="actionError" class="text-red-600 bg-red-50 p-3 rounded mb-4">
      {{ actionError }}
    </div>

    <!-- Create team -->
    <form @submit.prevent="handleCreateTeam" class="bg-white p-4 rounded-lg shadow mb-6 space-y-3">
      <h2 class="font-medium text-gray-700">New team</h2>
      <input
        v-model="newTeamName"
        type="text"
        placeholder="Team name"
        required
        class="w-full border border-gray-300 rounded px-3 py-2"
      />
      <input
        v-model="newTeamDescription"
        type="text"
        placeholder="Description (optional)"
        class="w-full border border-gray-300 rounded px-3 py-2"
      />
      <button type="submit" class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
        Create team
      </button>
    </form>

    <div v-if="teamsStore.loading" class="text-gray-500">Loading teams…</div>
    <div v-else-if="teamsStore.error" class="text-red-600 bg-red-50 p-3 rounded">
      {{ teamsStore.error }}
    </div>

    <!-- Team list -->
    <div v-else class="space-y-4">
      <div v-for="team in teamsStore.teams" :key="team.id" class="bg-white p-4 rounded-lg shadow">
        <h3 class="font-semibold text-gray-900">{{ team.name }}</h3>
        <p class="text-gray-500 text-sm mb-3">{{ team.description }}</p>

        <ul class="space-y-1 mb-3">
          <li
            v-for="m in team.memberships"
            :key="m.id"
            class="flex items-center justify-between text-sm text-gray-700"
          >
            <span>{{ m.username }} ({{ m.email }})</span>
            <button
              @click="handleRemoveMember(team.id, m.user)"
              class="text-red-600 hover:underline text-xs"
            >
              Remove
            </button>
          </li>
          <li v-if="team.memberships.length === 0" class="text-gray-400 text-sm">
            No members yet.
          </li>
        </ul>

        <!-- Add member by user ID for now — a proper user search/picker
             is a nice-to-have follow-up, not needed to prove the API
             works end to end. -->
        <div class="flex gap-2">
          <input
            v-model="newMemberUserId[team.id]"
            type="number"
            placeholder="User ID"
            class="border border-gray-300 rounded px-2 py-1 text-sm w-24"
          />
          <button
            @click="handleAddMember(team.id)"
            class="bg-gray-200 text-gray-800 px-3 py-1 rounded text-sm hover:bg-gray-300"
          >
            Add member
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
