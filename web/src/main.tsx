import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

// AG2 y ADR 0014: las fuentes las sirve la propia app. Las hojas `wdth` traen
// el eje de anchura, que es de lo que vive la identidad.
import '@fontsource-variable/archivo/wdth.css'
import '@fontsource-variable/archivo/wdth-italic.css'
import '@fontsource-variable/martian-mono/wdth.css'

import App from './App'
import './index.css'

const contenedor = document.getElementById('root')

if (!contenedor) {
  throw new Error('No existe el elemento #root en index.html')
}

createRoot(contenedor).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
