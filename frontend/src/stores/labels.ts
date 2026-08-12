import { defineStore } from 'pinia'
import client from '../api/client'

export interface Label {
  id: number
  board: number
  name: string
}

interface LabelsState {
  labels: Label[]
}

export const useLabelsStore = defineStore('labels', {
  state: (): LabelsState => ({
    labels: [],
  }),

  actions: {
    async fetchLabels(boardId: number) {
      const { data } = await client.get('/api/labels/', { params: { board: boardId } })
      this.labels = data
    },

    async createLabel(boardId: number, name: string) {
      const { data } = await client.post('/api/labels/', { board: boardId, name })
      this.labels.push(data)
    },

    async addLabelToIssue(issueId: number, labelId: number) {
      await client.post(`/api/issues/${issueId}/labels/`, { label: labelId })
    },

    async removeLabelFromIssue(issueId: number, labelId: number) {
      await client.delete(`/api/issues/${issueId}/labels/${labelId}`)
    },
  },
})
