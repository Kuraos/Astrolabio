import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// El frontend llama rutas relativas (`/api/...`) porque se sirve desde el
// mismo origen que la API (ADR 0005). No hay ninguna dirección aquí, y ese es
// justamente el criterio A3.
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
