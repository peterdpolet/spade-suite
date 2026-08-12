import { defineStore } from 'pinia'
import client from '../api/client'

export interface Activity {
  id: number
  board: number
  name: string
  planned_duration: number
  actual_duration: number | null
  parent: number | null
  created_at: string
}

export interface ActivityDependency {
  id: number
  predecessor: number
  successor: number
}

export interface BaselineActivitySchedule {
  id: number
  activity: number
  activity_name: string
  planned_duration_at_baseline: number
  early_start: number
  early_finish: number
  late_start: number
  late_finish: number
  float: number
}

export interface ScheduleBaseline {
  id: number
  board: number
  label: string
  created_at: string
  based_on: number | null
  is_active: boolean
  schedule: BaselineActivitySchedule[]
}

interface ActivitiesState {
  activities: Activity[]
  dependencies: ActivityDependency[]
  activeBaseline: ScheduleBaseline | null
  loading: boolean
  error: string | null
}

export const useActivitiesStore = defineStore('activities', {
  state: (): ActivitiesState => ({
    activities: [],
    dependencies: [],
    activeBaseline: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchAll(boardId: number) {
      this.loading = true
      this.error = null
      try {
        const [actRes, depRes, baselineRes] = await Promise.all([
          client.get('/api/activities/', { params: { board: boardId } }),
          client.get('/api/activity-dependencies/'),
          client.get('/api/baselines/', { params: { board: boardId } }),
        ])
        this.activities = actRes.data
        this.dependencies = depRes.data
        this.activeBaseline = baselineRes.data.find((b: ScheduleBaseline) => b.is_active) ?? null
      } catch (err: any) {
        this.error = 'Could not load project data.'
        throw err
      } finally {
        this.loading = false
      }
    },

    async createActivity(boardId: number, name: string, plannedDuration: number, parent: number | null = null) {
      const { data } = await client.post('/api/activities/', {
        board: boardId,
        name,
        planned_duration: plannedDuration,
        parent,
      })
      this.activities.push(data)
      return data
    },

    async createDependency(predecessor: number, successor: number) {
      const { data } = await client.post('/api/activity-dependencies/', { predecessor, successor })
      this.dependencies.push(data)
      return data
    },

    async createDecisionNode(boardId: number, label: string, rationale: string) {
      const { data } = await client.post('/api/decision-nodes/', { board: boardId, label, rationale })
      this.activeBaseline = data.resulting_baseline_detail
      return data
    },

    scheduleFor(activityId: number) {
      return this.activeBaseline?.schedule.find((s) => s.activity === activityId) ?? null
    },

    childrenOf(activityId: number) {
      return this.activities.filter((a) => a.parent === activityId)
    },

    // High-level roll-up for a top-level activity: if it has children,
    // its displayed span is the earliest child start to the latest
    // child finish — it is NEVER independently scheduled itself (the
    // CPM pass never runs on parent rows, only real leaf activities
    // and their real dependencies). "Critical" for a group is defined
    // as "at least one child is on the critical path" — a reasonable,
    // if debatable, definition worth stating explicitly rather than
    // leaving implicit.
    rollupFor(activityId: number) {
      const children = this.childrenOf(activityId)
      if (children.length === 0) {
        return this.scheduleFor(activityId)
      }
      const childSchedules = children.map((c) => this.scheduleFor(c.id)).filter(Boolean) as BaselineActivitySchedule[]
      if (childSchedules.length === 0) return null
      return {
        early_start: Math.min(...childSchedules.map((s) => s.early_start)),
        early_finish: Math.max(...childSchedules.map((s) => s.early_finish)),
        float: childSchedules.some((s) => s.float === 0) ? 0 : Math.min(...childSchedules.map((s) => s.float)),
      }
    },

    // For the high-level node diagram: an edge between two DIFFERENT
    // top-level groups exists if any of their children have a real
    // dependency between them. Edges where both ends resolve to the
    // SAME parent (an internal dependency within one group) are
    // dropped — they're not meaningful at this zoom level.
    promotedDependencies() {
      const ancestorOf = (id: number) => {
        const a = this.activities.find((x) => x.id === id)
        return a?.parent ?? id
      }
      const seen = new Set<string>()
      const result: { predecessor: number; successor: number }[] = []
      for (const dep of this.dependencies) {
        const p = ancestorOf(dep.predecessor)
        const s = ancestorOf(dep.successor)
        if (p === s) continue
        const key = `${p}-${s}`
        if (seen.has(key)) continue
        seen.add(key)
        result.push({ predecessor: p, successor: s })
      }
      return result
    },
  },
})