<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

interface ApiDiagram {
  id: number
  title: string
  team: number
  created_by: number
  created_at: string
}

const router = useRouter()
const diagrams = ref<ApiDiagram[]>([])
const newTitle = ref('')
const selectedTeam = ref<number | null>(null)
const teams = ref<Array<{ id: number; name: string }>>([])

async function loadDiagrams() {
  const response = await apiClient.get<ApiDiagram[]>('/api/diagrams/')
  diagrams.value = response.data
}

async function loadTeams() {
  const response = await apiClient.get('/api/teams/')
  teams.value = response.data
  if (teams.value.length > 0) {
    selectedTeam.value = teams.value[0].id
  }
}

async function createDiagram() {
  if (!newTitle.value.trim() || !selectedTeam.value) return
  const response = await apiClient.post<ApiDiagram>('/api/diagrams/', {
    title: newTitle.value,
    team: selectedTeam.value,
  })
  diagrams.value.push(response.data)
  newTitle.value = ''
  router.push({ name: 'diagram-detail', params: { id: response.data.id } })
}

function openDiagram(id: number) {
  router.push({ name: 'diagram-detail', params: { id } })
}

onMounted(() => {
  loadDiagrams()
  loadTeams()
})
</script>

<template>
  <div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-xl font-bold mb-4">Diagrams</h1>

    <div class="flex gap-2 mb-6">
      <select v-model="selectedTeam" class="border rounded px-2 py-1">
        <option v-for="team in teams" :key="team.id" :value="team.id">{{ team.name }}</option>
      </select>
      <input
        v-model="newTitle"
        placeholder="New diagram title"
        class="border rounded px-2 py-1 flex-1"
        @keyup.enter="createDiagram"
      />
      <button @click="createDiagram" class="bg-blue-600 text-white px-4 py-1 rounded">
        Create
      </button>
    </div>

    <ul class="space-y-2">
      <li
        v-for="diagram in diagrams"
        :key="diagram.id"
        @click="openDiagram(diagram.id)"
        class="border rounded p-3 cursor-pointer hover:bg-gray-50"
      >
        {{ diagram.title }}
      </li>
    </ul>
  </div>
</template>