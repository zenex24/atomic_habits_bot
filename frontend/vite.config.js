import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const base = process.env.VITE_BASE || process.env.GITHUB_PAGES_BASE || '/'

export default defineConfig({
  plugins: [react()],
  base,
})
