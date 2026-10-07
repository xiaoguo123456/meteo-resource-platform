import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { cpSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

function cesiumAssets() {
  return {
    name: 'copy-cesium-assets',
    configResolved() {
      const source = resolve(__dirname, 'node_modules/cesium/Build/Cesium')
      const target = resolve(__dirname, 'public/cesium')
      mkdirSync(target, { recursive: true })
      for (const directory of ['Assets', 'ThirdParty', 'Widgets', 'Workers']) {
        cpSync(resolve(source, directory), resolve(target, directory), { recursive: true })
      }
    },
  }
}

export default defineConfig({
  plugins: [vue(), cesiumAssets()],
  define: { CESIUM_BASE_URL: JSON.stringify('/cesium') },
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8000" } },
})
