import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@data': path.resolve(__dirname, '../data/synthetic'),
      '@configs': path.resolve(__dirname, '../configs'),
    },
  },
  server: {
    fs: {
      allow: ['..'],
    },
  },
  base: './',
})
