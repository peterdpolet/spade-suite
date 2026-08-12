<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{ label: string }>()
</script>

<template>
  <div class="event-node">
    <Handle type="target" :position="Position.Top" />
    <span>{{ label }}</span>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<style scoped>
.event-node {
  background: #fef3c7;
  border: 2px solid #d97706;
  border-radius: 20px;
  padding: 10px 16px;
  text-align: center;
  font-size: 13px;
  min-width: 120px;
}
</style>