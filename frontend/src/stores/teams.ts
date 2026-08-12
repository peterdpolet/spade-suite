import { defineStore } from 'pinia'
import client from '../api/client'

interface Membership {
  id: number
  user: number
  username: string
  email: string
  joined_at: string
}

interface Team {
  id: number
  name: string
  description: string
  memberships: Membership[]
  created_at: string
}

interface TeamsState {
  teams: Team[]
  loading: boolean
  error: string | null
}

export const useTeamsStore = defineStore('teams', {
  state: (): TeamsState => ({
    teams: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchTeams() {
      this.loading = true
      this.error = null
      try {
        const { data } = await client.get('/api/teams/')
        this.teams = data
      } catch (err: any) {
        this.error = 'Could not load teams.'
        throw err
      } finally {
        this.loading = false
      }
    },

    async createTeam(name: string, description: string) {
      const { data } = await client.post('/api/teams/', { name, description })
      this.teams.push(data)
    },

    async addMember(teamId: number, userId: number) {
      const { data } = await client.post(`/api/teams/${teamId}/members/`, { user: userId })
      const team = this.teams.find((t) => t.id === teamId)
      if (team) {
        team.memberships.push(data)
      }
    },

    async removeMember(teamId: number, userId: number) {
      await client.delete(`/api/teams/${teamId}/members/${userId}`)
      const team = this.teams.find((t) => t.id === teamId)
      if (team) {
        team.memberships = team.memberships.filter((m) => m.user !== userId)
      }
    },
  },
})
