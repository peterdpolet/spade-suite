<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')

async function handleSubmit() {
  try {
    await auth.login(email.value, password.value)
    router.push({ name: 'dashboard' })
  } catch {
    // auth.error is already set and shown in the template — nothing
    // further to do here.
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <form
      @submit.prevent="handleSubmit"
      class="w-full max-w-sm bg-white p-8 rounded-lg shadow space-y-4"
    >
      <h1 class="text-2xl font-semibold text-gray-900">Log in</h1>

      <div v-if="auth.error" class="text-sm text-red-600 bg-red-50 p-2 rounded">
        {{ auth.error }}
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">Email</label>
        <input
          v-model="email"
          type="email"
          required
          class="mt-1 w-full border border-gray-300 rounded px-3 py-2"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700">Password</label>
        <input
          v-model="password"
          type="password"
          required
          class="mt-1 w-full border border-gray-300 rounded px-3 py-2"
        />
      </div>

      <button
        type="submit"
        :disabled="auth.loading"
        class="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
      >
        {{ auth.loading ? 'Logging in…' : 'Log in' }}
      </button>

      <p class="text-sm text-gray-600 text-center">
        No account?
        <router-link :to="{ name: 'register' }" class="text-indigo-600 hover:underline">
          Register
        </router-link>
      </p>
    </form>
  </div>
</template>
