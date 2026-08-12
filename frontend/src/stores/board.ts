import { defineStore } from 'pinia'
import client from '../api/client'

interface Status {
  id: number
  name: string
  order: number
}

interface Board {
  id: number
  name: string
  description: string
  statuses: Status[]
  created_at: string
}

interface BoardState {
  board: Board | null
  loading: boolean
  error: string | null
}

export const useBoardStore = defineStore('board', {
  state: (): BoardState => ({
    board: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchBoard() {
      this.loading = true
      this.error = null
      try {
        // MVP is single-board — always take the first (and only) board.
        const { data } = await client.get('/api/boards/')
        this.board = data[0] ?? null
      } catch (err: any) {
        this.error = 'Could not load the board. Please try again.'
        throw err
      } finally {
        this.loading = false
      }
    },
  },
})
