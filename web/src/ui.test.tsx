/**
 * Criterio AP1 de la Fase 8: las pestañas, el patrón nuevo de `ui.tsx`.
 *
 * Como en `Guion.test.tsx`, se renderizan a HTML sin navegador: lo que se
 * comprueba es el marcado que sale, no cómo se ve.
 */

import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { Pestanas, pestanaTrasTecla } from './ui'

describe('pestanaTrasTecla', () => {
  it('las flechas pasan a la de al lado y dan la vuelta', () => {
    expect(pestanaTrasTecla(0, 3, 'ArrowRight')).toBe(1)
    expect(pestanaTrasTecla(2, 3, 'ArrowRight')).toBe(0)
    expect(pestanaTrasTecla(0, 3, 'ArrowLeft')).toBe(2)
  })

  it('Inicio y Fin van a los extremos', () => {
    expect(pestanaTrasTecla(1, 3, 'Home')).toBe(0)
    expect(pestanaTrasTecla(1, 3, 'End')).toBe(2)
  })

  it('las demás teclas no mueven', () => {
    expect(pestanaTrasTecla(1, 3, 'Enter')).toBeNull()
    expect(pestanaTrasTecla(1, 3, 'a')).toBeNull()
  })
})

describe('Pestanas', () => {
  const html = renderToStaticMarkup(
    <Pestanas
      grupo="textos"
      nombre="Textos de la pieza"
      pestanas={[
        { valor: 'guion', rotulo: 'Guion' },
        { valor: 'caption', rotulo: 'Caption' },
      ]}
      actual="caption"
      alElegir={() => {}}
    />,
  )
  const pestanas = html.match(/<button [^>]*>/g) ?? []

  it('dice cuál está elegida y qué panel controla cada una', () => {
    expect(html).toContain('role="tablist"')
    expect(pestanas[1]).toContain('aria-selected="true"')
    expect(pestanas[1]).toContain('aria-controls="textos-panel-caption"')
    expect(pestanas[0]).toContain('aria-selected="false"')
  })

  it('solo la elegida entra en el orden del Tab', () => {
    expect(pestanas[0]).toContain('tabindex="-1"')
    expect(pestanas[1]).toContain('tabindex="0"')
  })
})
