import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import path from 'path'

// 为 Edge 扩展构建时使用相对路径，避免 chrome-extension:// 协议下资源 404
const isExtensionBuild = process.env.VITE_EXTENSION_BUILD === 'true'

export default defineConfig({
  base: isExtensionBuild ? './' : '/',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    // Polling helps file-watch work reliably inside Docker volumes on Windows/macOS
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
