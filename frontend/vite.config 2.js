import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // GitHub Pages serves at https://<user>.github.io/<repo-name>/
  // so the asset base path must match the repo name.
  base: '/multi-agents-dispute-resolution/',
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
  },
})
