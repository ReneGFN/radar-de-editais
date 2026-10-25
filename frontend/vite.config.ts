/// <reference types="vitest/config" />
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// CSP restritiva só no build estático: em desenvolvimento o Vite injeta script inline (HMR).
const CSP = [
  "default-src 'none'", "script-src 'self'", "style-src 'self'", "img-src 'self'",
  "connect-src 'self'", "font-src 'self'", "base-uri 'none'", "form-action 'none'", "object-src 'none'",
].join('; ')

function staticCsp(): Plugin {
  return {
    name: 'radar-static-csp',
    apply: 'build',
    transformIndexHtml(html) {
      return html.replace('<!-- CSP -->', `<meta http-equiv="Content-Security-Policy" content="${CSP}">`)
    },
  }
}

export default defineConfig(({ mode, command }) => ({
  base: './',
  plugins: [react(), tailwindcss(), staticCsp()],
  // `site/` contém apenas `data/*.json` exportado por ops/export-site-data.py.
  publicDir: '../site',
  define: { __DATA_SOURCE__: JSON.stringify(mode === 'api' ? 'api' : 'static'),
            ...(mode === 'test' ? {} : { __CHAT_ENABLED__: JSON.stringify(command === 'serve') }) },
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    // Mesmo origin para a API local: sem CORS na API.
    proxy: { '/chat': { target: 'http://127.0.0.1:8766', changeOrigin: true },
             ...(mode === 'api' ? { '/api': { target: 'http://127.0.0.1:8765', changeOrigin: false } } : {}) },
  },
  build: { outDir: 'dist', emptyOutDir: true, sourcemap: false },
  test: { environment: 'jsdom', globals: false },
}))
