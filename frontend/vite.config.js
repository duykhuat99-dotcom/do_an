import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Frontend gọi backend qua biến VITE_API_BASE_URL (mặc định http://localhost:8000).
// Ngoài ra cấu hình proxy /api -> backend để tránh CORS khi phát triển.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
