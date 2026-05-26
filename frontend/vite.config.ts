import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
// visualizer removed after analysis

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // Treat Element Plus icons as custom elements to suppress warnings
          isCustomElement: (tag) => tag.startsWith('El')
        }
      }
    }),
    // Auto-import Vue APIs (ref, computed, etc.) and ElementPlus resolvers
    AutoImport({
      resolvers: [
        ElementPlusResolver({ import: true, directives: true }),
      ],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [
        ElementPlusResolver({
          importStyle: 'css',
        }),
      ],
      dts: 'src/components.d.ts',
    }),

  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    open: false,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Element Plus per-component chunks (already split, keep pattern)
            if (id.includes('element-plus/es/components')) {
              const match = id.match(/element-plus\/es\/components\/([^/]+)/)
              if (match) {
                return `ep-${match[1]}`
              }
            }
            // Element Plus core utilities
            if (id.includes('element-plus/es/hooks') ||
                id.includes('element-plus/es/utils') ||
                id.includes('element-plus/es/locale')) {
              return 'element-plus-core'
            }
            // Icons
            if (id.includes('@element-plus/icons-vue')) return 'ep-icons'
            // Echarts
            if (id.includes('echarts')) return 'echarts'
            // Core framework - split Vue, Vue-Router, Pinia into separate chunks
            if (id.includes('/vue/')) return 'vue'
            if (id.includes('/pinia/')) return 'pinia'
            if (id.includes('/vue-router/')) return 'vue-router'
            // VueUse with Pinia
            if (id.includes('@vueuse')) return 'vueuse'
            // Axios (HTTP client, stable - good for long-term caching)
            if (id.includes('axios')) return 'axios'
            // dayjs (date library, stable - good for caching)
            if (id.includes('dayjs')) return 'dayjs'
            // Element Plus main package (remaining parts)
            if (id.includes('element-plus')) return 'element-plus'
            // Markdown (if any)
            if (id.includes('markdown') || id.includes('marked')) return 'markdown'
            return 'vendor'
          }
        }
      }
    }
  },
  esbuild: {
    keepNames: true
  },
  // Suppress third-party type errors
  exclude: ['**/node_modules/**']
})
