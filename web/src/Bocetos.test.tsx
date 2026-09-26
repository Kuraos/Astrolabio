/**
 * Criterios AV2 y AV3 de la Fase 9: la lámina se dibuja desde los datos, y lo
 * que escribe el modelo no se interpreta como HTML (ADR 0016).
 *
 * Como en `Guion.test.tsx`, se renderiza a HTML sin navegador: lo que se
 * comprueba es el marcado que sale, no cómo se ve.
 */

import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import type { LaminaDelBoceto } from './api'
import { LaminaDeBoceto } from './Bocetos'

const lamina: LaminaDelBoceto = {
  numero: 2,
  idea: 'La distancia al Sol, en una fórmula',
  elementos: [
    {
      tipo: 'texto',
      peso: 2,
      contenido: 'Recorre',
      zona: { fila: 9, col: 2, filas: 3, cols: 10 },
    },
    {
      tipo: 'formula',
      peso: 1,
      contenido: 'd \\approx 1{,}496 \\times 10^{11}\\,\\mathrm{m}',
      zona: { fila: 3, col: 2, filas: 5, cols: 10 },
    },
    {
      tipo: 'figura',
      peso: 4,
      contenido: 'El Sol en ultravioleta',
      zona: { fila: 13, col: 2, filas: 2, cols: 4 },
    },
  ],
  nota_para_la_edicion: 'La fórmula, grande y sola.',
}

const pintar = (l: LaminaDelBoceto, columnas = 12, filas = 15) =>
  renderToStaticMarkup(<LaminaDeBoceto lamina={l} columnas={columnas} filas={filas} />)

describe('AV2: la lámina, desde los datos', () => {
  const html = pintar(lamina)

  it('en su proporción y con su rejilla', () => {
    expect(html).toContain('aspect-ratio:12 / 15')
    expect(html).toContain('grid-template-columns:repeat(12, minmax(0, 1fr))')
    expect(html).toContain('grid-template-rows:repeat(15, minmax(0, 1fr))')
  })

  it('cada elemento, en su zona', () => {
    expect(html).toContain('grid-column:2 / span 10;grid-row:3 / span 5')
    expect(html).toContain('grid-column:2 / span 4;grid-row:13 / span 2')
  })

  it('el de peso 1 se lee primero, aunque llegue después', () => {
    expect(html.indexOf('Fórmula · 1')).toBeLessThan(html.indexOf('Texto · 2'))
  })

  it('la fórmula sale con KaTeX, y la figura con su aspa', () => {
    expect(html).toContain('class="katex"')
    expect(html).toMatch(/<svg aria-hidden="true"[^>]*><line/)
  })

  it('la idea arriba y la nota para la edición abajo (AV3)', () => {
    expect(html.indexOf(lamina.idea)).toBeLessThan(html.indexOf('grid-template-columns'))
    expect(html.indexOf('La fórmula, grande y sola.')).toBeGreaterThan(
      html.indexOf('grid-template-columns'),
    )
  })

  it('el póster, en 12 × 17', () => {
    expect(pintar(lamina, 12, 17)).toContain('aspect-ratio:12 / 17')
  })

  it('en una zona de una fila, el rótulo y el texto van en línea', () => {
    const nota: LaminaDelBoceto = {
      ...lamina,
      elementos: [
        { tipo: 'nota', peso: 1, contenido: 'Imagen: NASA/SDO', zona: { fila: 14, col: 2, filas: 1, cols: 6 } },
      ],
    }

    expect(pintar(nota)).toMatch(/class="relative flex[^"]*flex-row[^"]*"[^>]*grid-row:14 \/ span 1/)
    expect(pintar(lamina)).not.toContain('flex-row')
  })
})

describe('lo que escribe el modelo no es HTML', () => {
  const trampa = '<img src=x onerror="alert(1)"><script>alert(2)</script>'
  const conTrampa = (tipo: string): LaminaDelBoceto => ({
    ...lamina,
    idea: trampa,
    nota_para_la_edicion: trampa,
    elementos: [{ tipo, peso: 1, contenido: trampa, zona: { fila: 1, col: 1, filas: 2, cols: 2 } }],
  })

  it.each(['texto', 'titulo', 'figura', 'formula'])('ni en un elemento de tipo %s', (tipo) => {
    const html = pintar(conTrampa(tipo))

    expect(html).not.toContain('<img')
    expect(html).not.toContain('<script')
  })
})
