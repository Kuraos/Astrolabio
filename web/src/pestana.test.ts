/**
 * Criterios AZ1 y AZ2 de la Fase 10: el título de la pestaña y la recarga que
 * solo corre mientras la pestaña se ve. Con un documento de mentira y el reloj
 * de vitest: sin navegador.
 */

import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'

import type { Usuario } from './api'
import { cuantasTeTocan } from './flujo'
import { CADA, recargarMientrasSeVe, tituloDeLaPestana } from './pestana'
import { piezaDePrueba } from './piezaDePrueba'

describe('AZ1: el título de la pestaña', () => {
  it('lleva cuántas te tocan', () => {
    expect(tituloDeLaPestana(1)).toBe('(1) Astrolabio')
    expect(tituloDeLaPestana(12)).toBe('(12) Astrolabio')
  })

  it('sin nada que te toque, la marca a secas', () => {
    expect(tituloDeLaPestana(0)).toBe('Astrolabio')
  })

  it('cuenta las mismas que el bloque naranja: las del rol de quien mira', () => {
    const piezas = [
      piezaDePrueba({ id: 1, de_quien_es: 'investigador' }),
      piezaDePrueba({ id: 2, de_quien_es: 'editor' }),
      piezaDePrueba({ id: 3, de_quien_es: 'editor' }),
      piezaDePrueba({ id: 4, estado: 'publicada', de_quien_es: null }),
    ]
    const editor: Usuario = { usuario: 'dathzon', rol: 'editor' }
    const johan: Usuario = { usuario: 'johan', rol: 'investigador' }

    expect(cuantasTeTocan(piezas, editor)).toBe(2)
    expect(cuantasTeTocan(piezas, johan)).toBe(1)
  })
})

describe('AZ2: la recarga, solo mientras la pestaña se ve', () => {
  let pagina: EventTarget & { visibilityState: DocumentVisibilityState }
  let recargar: Mock<() => void>

  function cambiarA(visibilidad: DocumentVisibilityState) {
    pagina.visibilityState = visibilidad
    pagina.dispatchEvent(new Event('visibilitychange'))
  }

  beforeEach(() => {
    vi.useFakeTimers()
    pagina = Object.assign(new EventTarget(), { visibilityState: 'visible' as DocumentVisibilityState })
    recargar = vi.fn<() => void>()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('cada minuto mientras se ve', () => {
    recargarMientrasSeVe(recargar, pagina)

    vi.advanceTimersByTime(CADA - 1)
    expect(recargar).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(recargar).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(2 * CADA)
    expect(recargar).toHaveBeenCalledTimes(3)
  })

  it('oculta, ni un pedido', () => {
    recargarMientrasSeVe(recargar, pagina)
    cambiarA('hidden')

    vi.advanceTimersByTime(10 * CADA)

    expect(recargar).not.toHaveBeenCalled()
  })

  it('al volver a verse, enseguida, sin esperar al minuto', () => {
    recargarMientrasSeVe(recargar, pagina)
    cambiarA('hidden')
    vi.advanceTimersByTime(5 * CADA)

    cambiarA('visible')

    expect(recargar).toHaveBeenCalledTimes(1)
  })

  it('al dejar de vigilar, se acaba: ni el reloj ni la pestaña', () => {
    const dejar = recargarMientrasSeVe(recargar, pagina)
    dejar()

    vi.advanceTimersByTime(3 * CADA)
    cambiarA('hidden')
    cambiarA('visible')

    expect(recargar).not.toHaveBeenCalled()
  })
})
