<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{ label: string }>()
</script>

<template>
  <div class="org-unit-node">
    <Handle type="target" :position="Position.Left" />
    <span>{{ label }}</span>
    <Handle type="source" :position="Position.Right" />
  </div>
</template>

<style scoped>
.org-unit-node {
  background: #ede9fe;
  border: 2px solid #7c3aed;
  border-radius: 50px;
  padding: 10px 20px;
  text-align: center;
  font-size: 13px;
  min-width: 120px;
}
</style>