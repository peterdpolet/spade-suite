<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{ label: string }>()
</script>

<template>
  <div class="data-object-node">
    <Handle type="target" :position="Position.Left" />
    <span>{{ label }}</span>
    <Handle type="source" :position="Position.Right" />
  </div>
</template>

<style scoped>
.data-object-node {
  background: #dcfce7;
  border: 2px solid #16a34a;
  border-radius: 4px;
  padding: 10px 16px;
  text-align: center;
  font-size: 13px;
  min-width: 120px;
  position: relative;
}

.data-object-node::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 10px 10px 0;
  border-color: transparent white transparent transparent;
}
</style>