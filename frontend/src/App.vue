<script setup lang="ts">
// Board/issue views land in Modules 3-8 — this is the Module 1 shell only.
</script>

<template>
  <div class="min-h-screen">
    <header class="flex items-center gap-3 px-7 py-4 bg-teal-dark text-paper">
      <div class="w-6 h-6 bg-ochre rounded flex items-center justify-center font-display font-bold text-sm text-teal-dark">m</div>
      <div>
        <div class="font-display font-semibold text-lg">miniJira</div>
        <div class="text-xs text-teal-tint opacity-80">the tools to get from idea to delivery — without the tool stack becoming the project</div>
      </div>
    </header>
    <main class="p-7">
      <router-view />
    </main>
  </div>
</template>
