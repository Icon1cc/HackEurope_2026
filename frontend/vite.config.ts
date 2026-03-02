import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react(), tailwindcss()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  assetsInclude: ['**/*.svg', '**/*.csv'],

  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      external: ['@stripe/stripe-js', '@stripe/react-stripe-js'],
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router'],
          charts: ['recharts', 'react-circular-progressbar'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-tooltip'],
          mui: ['@mui/material', '@mui/icons-material'],
        },
      },
    },
  },

  server: {
    port: 3000,
    strictPort: false,
    open: true,
    proxy: {
      // Proxy @paid-ai/paid-blocks component requests to FastAPI backend.
      // Components call /api/{endpoint}/{customerExternalId} (Next.js pattern).
      // Existing frontend uses absolute URLs (http://127.0.0.1:8000/...) so no conflict.
      '/api/usage': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/usage/, '/api/v1/paid-blocks/usage'),
      },
      '/api/invoices': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/invoices/, '/api/v1/paid-blocks/invoices'),
      },
    },
  },

  preview: {
    port: 4173,
    open: true,
  },
})
