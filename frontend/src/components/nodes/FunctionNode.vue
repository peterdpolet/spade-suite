<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{ label: string }>()
</script>

<template>
  <div class="function-node">
    <Handle type="target" :position="Position.Top" id="top" />
    <Handle type="source" :position="Position.Bottom" id="bottom" />
    <Handle type="target" :position="Position.Left" id="left" />
    <Handle type="source" :position="Position.Right" id="right" />
    <span>{{ label }}</span>
  </div>
</template>

<style scoped>
.function-node {
  background: #dbeafe;
  border: 2px solid #2563eb;
  border-radius: 4px;
  padding: 10px 16px;
  text-align: center;
  font-size: 13px;
  min-width: 120px;
}
</style>