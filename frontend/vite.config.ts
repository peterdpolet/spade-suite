import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      // WebSocket traffic goes to a separate Daphne process on 8001 —
      // mirrors the production split (nginx routes /ws/ to the daphne
      // container, /api/ to the gunicorn container; two processes, two
      // roles, same reasoning here for local dev).
      '/ws': {
        target: 'ws://127.0.0.1:8001',
        ws: true,
      },
    },
  },
})
