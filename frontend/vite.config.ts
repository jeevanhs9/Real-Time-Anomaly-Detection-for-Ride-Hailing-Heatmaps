import react from '@vitejs/plugin-react'
import { defineConfig, type UserConfig } from 'vite'

const config = {
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws':  { target: 'ws://localhost:8000',  ws: true },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
} satisfies UserConfig & {
  test: {
    globals: boolean
    environment: string
    setupFiles: string[]
  }
}

export default defineConfig(config)
