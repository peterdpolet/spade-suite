import { defineStore } from 'pinia'
import client from '../api/client'

export interface Issue {
  id: number
  board: number
  status: number
  title: string
  description: string
  priority: 'low' | 'medium' | 'high'
  team: number | null
  assignee: number | null
  target_completion_date: string | null
  actual_completion_date: string | null
  order: string
  labels: { id: number; board: number; name: string }[]
  created_at: string
  updated_at: string
}

export interface IssueFilters {
  status?: number
  assignee?: number
  label?: number
  search?: string
}

interface IssuesState {
  issues: Issue[]
  loading: boolean
  error: string | null
}

export const useIssuesStore = defineStore('issues', {
  state: (): IssuesState => ({
    issues: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchIssues(boardId: number, filters: IssueFilters = {}) {
      this.loading = true
      this.error = null
      try {
        const { data } = await client.get('/api/issues/', {
          params: { board: boardId, ...filters },
        })
        this.issues = data
      } catch (err: any) {
        this.error = 'Could not load issues.'
        throw err
      } finally {
        this.loading = false
      }
    },

    async createIssue(payload: Partial<Issue>) {
      const { data } = await client.post('/api/issues/', payload)
      this.issues.push(data)
      return data
    },

    async updateIssue(id: number, payload: Partial<Issue>) {
      const { data } = await client.patch(`/api/issues/${id}/`, payload)
      const index = this.issues.findIndex((i) => i.id === id)
      if (index !== -1) {
        this.issues[index] = data
      }
      return data
    },

    // PLANTED BUG (Module 10, deliberate — see
    // Spadework_Tier2_Kanban_Spec_v1.md "Planted teaching bugs"):
    // optimistic UI. The card's status is updated in local state
    // IMMEDIATELY, before the server confirms anything — that's what
    // makes drag-and-drop feel instant instead of laggy. But it means
    // there's a real window where the UI shows something that isn't
    // true yet. If the API call fails, we roll back to the snapshot —
    // but this rollback is itself naive: it doesn't account for other
    // realtime events that may have arrived and mutated this same
    // issue DURING the pending request, so a badly-timed rollback can
    // overwrite a legitimate concurrent update with stale snapshot
    // data. That's the actual teaching bug, not just "sometimes shows
    // a spinner."
    async reorderIssue(id: number, statusId: number, beforeId?: number, afterId?: number) {
      const index = this.issues.findIndex((i) => i.id === id)
      if (index === -1) return
      const snapshot = { ...this.issues[index] }

      // Optimistic: apply immediately, don't wait for the server.
      this.issues[index] = { ...this.issues[index], status: statusId }

      try {
        const { data } = await client.post(`/api/issues/${id}/reorder/`, {
          status: statusId,
          before_id: beforeId,
          after_id: afterId,
        })
        const i = this.issues.findIndex((i) => i.id === id)
        if (i !== -1) this.issues[i] = data
      } catch (err) {
        // Rollback — naive, see docstring above.
        const i = this.issues.findIndex((i) => i.id === id)
        if (i !== -1) this.issues[i] = snapshot
        throw err
      }
    },

    applyRealtimeEvent(event: 'created' | 'updated' | 'deleted', issue: any) {
      const index = this.issues.findIndex((i) => i.id === issue.id)
      if (event === 'deleted') {
        if (index !== -1) this.issues.splice(index, 1)
        return
      }
      if (index !== -1) {
        this.issues[index] = issue
      } else {
        this.issues.push(issue)
      }
    },
  },
})