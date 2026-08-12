<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

onMounted(async () => {
  if (!auth.user) {
    try {
      await auth.fetchUser()
    } catch {
      router.push({ name: 'login' })
    }
  }
})

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 p-8">
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
      <h1 class="text-2xl font-semibold text-gray-900 mb-4">Dashboard</h1>

      <div v-if="auth.user" class="space-y-2">
        <p class="text-gray-700">Logged in as <strong>{{ auth.user.email }}</strong></p>
        <p class="text-gray-500 text-sm">Username: {{ auth.user.username }}</p>
      </div>
      <p v-else class="text-gray-500">Loading…</p>

      <div class="mt-6 flex gap-3">
        <router-link
          :to="{ name: 'board' }"
          class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
        >
          View Board
        </router-link>
        <router-link
          :to="{ name: 'teams' }"
          class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
        >
          Teams
        </router-link>
        <router-link
          :to="{ name: 'project' }"
          class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
        >
          Project Schedule
        </router-link>

        <router-link
          :to="{ name: 'diagram-list' }"
          class="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
        >
          Diagrams
        </router-link>


        <button
          @click="handleLogout"
          class="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
        >
          Log out
        </button>



      </div>
    </div>
  </div>
</template>
