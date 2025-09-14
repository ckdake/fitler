import { defineConfig } from 'vite'
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  root: 'src',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'src/index.html'
      }
    }
  },
  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11']
    })
  ],
  server: {
    host: '0.0.0.0',
    port: 3000
  }
})
