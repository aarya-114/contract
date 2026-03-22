import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/pdf': 'http://localhost:8000',      // ← ADD THIS
      '/search': 'http://localhost:8000',
    }
  }
})