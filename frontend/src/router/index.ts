import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/board',
    name: 'board',
    component: () => import('../views/BoardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/teams',
    name: 'teams',
    component: () => import('../views/TeamsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/project',
    name: 'project',
    component: () => import('../views/ProjectView.vue'),
    meta: { requiresAuth: true },
  },

  {
  path: '/diagrams',
  name: 'diagram-list',
  component: () => import('@/views/DiagramListView.vue'),
  meta: { requiresAuth: true },
  },

  {
  path: '/diagrams/:id',
  name: 'diagram-detail',
  component: () => import('@/views/DiagramView.vue'),
  },

]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }
  if (to.meta.requiresGuest && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }
})

export default router
