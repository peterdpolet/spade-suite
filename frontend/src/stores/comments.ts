import { defineStore } from 'pinia'
import client from '../api/client'

interface Comment {
  id: number
  issue: number
  author: number
  author_username: string
  body: string
  created_at: string
}

interface CommentsState {
  // Keyed by issue id — NOT a single flat list. A flat list was the
  // bug: with two IssueForm instances mounted at once (e.g. an "add"
  // form and an "edit" form open simultaneously), both read/wrote the
  // same shared array, so one form's comments leaked into the other's
  // display.
  commentsByIssue: Record<number, Comment[]>
  loading: boolean
}

export const useCommentsStore = defineStore('comments', {
  state: (): CommentsState => ({
    commentsByIssue: {},
    loading: false,
  }),

  actions: {
    async fetchComments(issueId: number) {
      this.loading = true
      try {
        const { data } = await client.get('/api/comments/', { params: { issue: issueId } })
        this.commentsByIssue[issueId] = data
      } finally {
        this.loading = false
      }
    },

    async postComment(issueId: number, body: string) {
      const { data } = await client.post('/api/comments/', { issue: issueId, body })
      if (!this.commentsByIssue[issueId]) {
        this.commentsByIssue[issueId] = []
      }
      this.commentsByIssue[issueId].push(data)
    },
  },
})
