<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import apiClient from '@/api/client'

import EventNode from '@/components/nodes/EventNode.vue'
import FunctionNode from '@/components/nodes/FunctionNode.vue'
import OrgUnitNode from '@/components/nodes/OrgUnitNode.vue'
import DataObjectNode from '@/components/nodes/DataObjectNode.vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'

interface ApiNode {
  id: number
  node_type: string
  label: string
  position_x: number
  position_y: number
  parent_node: number | null
}

interface ApiEdge {
  id: number
  source_node: number
  target_node: number
}


interface SelectedElement {
  kind: 'node' | 'edge'
  id: string
  label?: string
}

const selected = ref<SelectedElement | null>(null)
const editLabel = ref('')

function selectNode(node: { id: string; label?: string }) {
  selected.value = { kind: 'node', id: node.id, label: node.label }
  editLabel.value = node.label ?? ''
}

function selectEdge(edge: { id: string }) {
  selected.value = { kind: 'edge', id: edge.id }
}

function clearSelection() {
  selected.value = null
}

async function saveLabel() {
  if (!selected.value || selected.value.kind !== 'node') return
  await apiClient.patch(`/api/nodes/${selected.value.id}/`, { label: editLabel.value })
  const node = findNode(selected.value.id)
  if (node) node.label = editLabel.value
  clearSelection()
}

async function deleteSelected() {
  if (!selected.value) return
  if (selected.value.kind === 'node') {
    const nodeId = selected.value.id
    await apiClient.delete(`/api/nodes/${nodeId}/`)
    removeNodes([nodeId])

    const attachedEdges = edges.value.filter(
      (e) => e.source === nodeId || e.target === nodeId
    )
    if (attachedEdges.length > 0) {
      removeEdges(attachedEdges.map((e) => e.id))
    }
  } else {
    await apiClient.delete(`/api/edges/${selected.value.id}/`)
    removeEdges([selected.value.id])
  }
  clearSelection()
}


const route = useRoute()
const diagramId = route.params.id

const { nodes, edges, addNodes, addEdges, removeNodes, removeEdges, onConnect, findNode } = useVueFlow()

const nodeTypes = {
  event: EventNode,
  function: FunctionNode,
  org_unit: OrgUnitNode,
  data_object: DataObjectNode,
}

const allowedConnections: Record<string, string[]> = {
  event: ['function'],
  function: ['event', 'org_unit', 'data_object'],
  org_unit: ['function'],
  data_object: ['function'],
}

function isValidConnection(connection: { source: string; target: string }) {
  const sourceNode = findNode(connection.source)
  const targetNode = findNode(connection.target)
  if (!sourceNode || !targetNode) return false
  return allowedConnections[sourceNode.data.nodeType]?.includes(targetNode.data.nodeType) ?? false
}

// Breadcrumb trail: null = top level. Each entry is { id, label } of the parent drilled into.
const breadcrumb = ref<Array<{ id: number; label: string }>>([])
const currentParentId = ref<number | null>(null)

async function loadDiagram() {
  removeNodes(nodes.value)
  removeEdges(edges.value)

  const parentParam = currentParentId.value === null ? '' : String(currentParentId.value)

  const [nodesResponse, edgesResponse] = await Promise.all([
    apiClient.get<ApiNode[]>(`/api/nodes/?diagram=${diagramId}&parent=${parentParam}`),
    apiClient.get<ApiEdge[]>(`/api/edges/?diagram=${diagramId}`),
  ])

  const visibleNodeIds = new Set(nodesResponse.data.map((n) => n.id))

  const vueFlowNodes = nodesResponse.data.map((n) => ({
    id: String(n.id),
    type: n.node_type,
    label: n.label,
    position: { x: n.position_x, y: n.position_y },
    data: { nodeType: n.node_type },
  }))
  addNodes(vueFlowNodes)

  const vueFlowEdges = edgesResponse.data
    .filter((e) => visibleNodeIds.has(e.source_node) && visibleNodeIds.has(e.target_node))
    .map((e) => ({
      id: `e${e.id}`,
      source: String(e.source_node),
      target: String(e.target_node),
    }))
  addEdges(vueFlowEdges)
}

function drillInto(node: { id: string; data: { label?: string }; label?: string }) {
  breadcrumb.value.push({ id: Number(node.id), label: node.label ?? '' })
  currentParentId.value = Number(node.id)
  loadDiagram()
}

function drillTo(index: number) {
  if (index === -1) {
    breadcrumb.value = []
    currentParentId.value = null
  } else {
    breadcrumb.value = breadcrumb.value.slice(0, index + 1)
    currentParentId.value = breadcrumb.value[index].id
  }
  loadDiagram()
}

async function addNode(nodeType: string) {
  const response = await apiClient.post('/api/nodes/', {
    diagram: diagramId,
    node_type: nodeType,
    label: 'New node',
    position_x: 200,
    position_y: 200,
    parent_node: currentParentId.value,
  })
  addNodes([{
    id: String(response.data.id),
    type: response.data.node_type,
    label: response.data.label,
    position: { x: response.data.position_x, y: response.data.position_y },
    data: { nodeType: response.data.node_type },
  }])
}



onConnect((connection) => {
  apiClient.post('/api/edges/', {
    diagram: diagramId,
    source_node: Number(connection.source),
    target_node: Number(connection.target),
  }).then((response) => {
    addEdges([{ id: `e${response.data.id}`, source: connection.source, target: connection.target }])
  }).catch((error) => {
    console.error('Failed to save edge:', error)
  })
})

let socket: WebSocket | null = null

function connectWebSocket() {
  socket = new WebSocket(`ws://127.0.0.1:8001/ws/diagram/${diagramId}/`)

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data)
    const { event: eventType, entity, data } = payload

    if (entity === 'node' && eventType === 'created') {
      const belongsToCurrentLevel = data.parent_node === currentParentId.value
      if (belongsToCurrentLevel && !findNode(String(data.id))) {
        addNodes([{
          id: String(data.id),
          type: data.node_type,
          label: data.label,
          position: { x: data.position_x, y: data.position_y },
          data: { nodeType: data.node_type },
        }])
      }
    }

    if (entity === 'edge' && eventType === 'created') {
      const sourceExists = findNode(String(data.source_node))
      const targetExists = findNode(String(data.target_node))
      if (sourceExists && targetExists) {
        addEdges([{
          id: `e${data.id}`,
          source: String(data.source_node),
          target: String(data.target_node),
        }])
      }
    }
  }

  socket.onclose = () => {
    console.log('WebSocket closed, will not auto-reconnect (v1 scope)')
  }
}

onMounted(() => {
  loadDiagram()
  connectWebSocket()
})

onUnmounted(() => {
  socket?.close()
})
</script>


<template>
  <div class="h-screen w-full flex flex-col">
    <div class="p-2 bg-gray-100 flex gap-2 items-center text-sm">
      <button @click="drillTo(-1)" class="underline">Top level</button>
      <span v-for="(crumb, i) in breadcrumb" :key="crumb.id">
        / <button @click="drillTo(i)" class="underline">{{ crumb.label }}</button>
      </span>
    </div>

    <div class="p-2 bg-white border-b flex gap-2 text-sm">
      <button @click="addNode('event')" class="px-3 py-1 rounded border" style="background:#fef3c7;border-color:#d97706">+ Event</button>
      <button @click="addNode('function')" class="px-3 py-1 rounded border" style="background:#dbeafe;border-color:#2563eb">+ Function</button>
      <button @click="addNode('org_unit')" class="px-3 py-1 rounded border" style="background:#ede9fe;border-color:#7c3aed">+ Org Unit</button>
      <button @click="addNode('data_object')" class="px-3 py-1 rounded border" style="background:#dcfce7;border-color:#16a34a">+ Data Object</button>
  </div>

    <div class="flex-1">
      
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :node-types="nodeTypes"
      :is-valid-connection="isValidConnection"
      @node-double-click="(e) => drillInto(e.node)"
      @node-click="(e) => selectNode(e.node)"
      @edge-click="(e) => selectEdge(e.edge)"
      @pane-click="clearSelection"
    >
      <template #node-event="props"><EventNode :label="props.label" /></template>
      <template #node-function="props"><FunctionNode :label="props.label" /></template>
      <template #node-org_unit="props"><OrgUnitNode :label="props.label" /></template>
      <template #node-data_object="props"><DataObjectNode :label="props.label" /></template>
      <Background />
      <Controls />
    </VueFlow>

    <div v-if="selected" class="fixed bottom-4 right-4 bg-white border rounded shadow p-3 flex gap-2 items-center">
      <input
        v-if="selected.kind === 'node'"
        v-model="editLabel"
        class="border rounded px-2 py-1 text-sm"
        @keyup.enter="saveLabel"
      />
      <button v-if="selected.kind === 'node'" @click="saveLabel" class="bg-blue-600 text-white px-3 py-1 rounded text-sm">
        Save
      </button>
      <button @click="deleteSelected" class="bg-red-600 text-white px-3 py-1 rounded text-sm">
        Delete
      </button>
    </div>


    </div>
  </div>
</template>