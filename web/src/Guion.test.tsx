/**
 * Criterios V1 y V2 de la Fase 4: lo que pinta la vista previa del guion.
 *
 * Se renderiza a HTML con `react-dom/server`, sin navegador ni jsdom: lo que
 * se comprueba es el marcado que sale, no cómo se ve.
 */

import katex from 'katex'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'

import { VistaPrevia } from './Guion'

const pintar = (texto: string) => renderToStaticMarkup(<VistaPrevia texto={texto} />)

/** Las etiquetas `<a …>` del HTML, para mirar sus atributos. */
const enlaces = (html: string) => html.match(/<a [^>]*>/g) ?? []

describe('V1: la vista previa pinta lo mismo que Obsidian', () => {
  it('pinta las tablas', () => {
    expect(pintar('| Magnitud | Valor |\n| --- | --- |\n| Masa | 1 |')).toContain('<table>')
  })

  it('tacha con dos virgulillas', () => {
    expect(pintar('~~descartado~~')).toContain('<del>descartado</del>')
  })

  it('las notas al pie se rotulan en español', () => {
    const html = pintar('Texto[^1].\n\n[^1]: La fuente.')

    expect(html).toContain('>Notas</h2>')
    expect(html).not.toContain('Footnotes')
  })

  it('una virgulilla sola no tacha', () => {
    // Obsidian documenta el tachado con dos. En un guion de física, `~10`
    // es «aproximadamente diez».
    expect(pintar('entre ~10~ y ~20 estrellas')).not.toContain('<del>')
  })
})

describe('Las fórmulas se pintan con el KaTeX que trae el CSS', () => {
  it('las clases de tamaño coinciden', () => {
    // `rehype-katex` pinta con su KaTeX, y el CSS lo trae el paquete `katex`
    // (Guion.tsx). Si las dos versiones se separan, las clases cambian de
    // nombre y el CSS no las encuentra: con el HTML de 0.16, que dice
    // `sizing`, y el CSS de 0.18, que dice `katex-sizing`, los subíndices
    // salían a tamaño completo.
    const claseDeTamano = (html: string) => html.match(/class="(\S+) reset-size/)?.[1]

    expect(claseDeTamano(pintar('$m_1$'))).toBe(
      claseDeTamano(katex.renderToString('m_1', { output: 'html' })),
    )
  })
})

describe('V2: los enlaces se abren en otra pestaña', () => {
  it('un enlace sale con target y rel', () => {
    const [enlace] = enlaces(pintar('[el paper](https://arxiv.org/abs/1234.5678)'))

    expect(enlace).toContain('target="_blank"')
    expect(enlace).toContain('rel="noopener noreferrer"')
  })

  it('la llamada a una nota al pie se queda en la misma pestaña', () => {
    // Es un ancla de la propia vista previa: abrirla en otra pestaña la rompe.
    const html = pintar('Texto[^1].\n\n[^1]: La fuente.')
    const llamada = enlaces(html).find((a) => a.includes('href="#user-content-fn-1"'))

    expect(llamada).toBeDefined()
    expect(llamada).not.toContain('target=')
  })
})
