/**
 * Criterio AG1 de la Fase 7: la paleta por defecto de Tailwind está vacía
 * (`index.css`), así que una clase suya olvidada no pintaría nada y la
 * pantalla se vería mal sin que nada fallara. Esta prueba es lo que falla.
 */

import { expect, it } from 'vitest'

const fuentes = import.meta.glob<string>(['./**/*.{ts,tsx}', '!./**/*.test.*'], {
  query: '?raw',
  import: 'default',
  eager: true,
})

const PALETA =
  /\b(?:bg|text|border|divide|ring|outline|accent|decoration|fill|stroke|placeholder)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|black|white)\b/g

it('ninguna pantalla usa un color de la paleta por defecto de Tailwind', () => {
  const restos = Object.entries(fuentes).flatMap(([archivo, texto]) =>
    [...texto.matchAll(PALETA)].map(([clase]) => `${archivo}: ${clase}`),
  )
  expect(restos).toEqual([])
})

it('mira de verdad los archivos del cliente', () => {
  expect(Object.keys(fuentes)).toContain('./App.tsx')
})
