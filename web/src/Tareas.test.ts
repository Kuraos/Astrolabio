/**
 * Criterios AD6 y AD7 de la Fase 6: cuántas tareas le quedan a una pieza, de
 * cuántas, dicho como se diría.
 */

import { describe, expect, it } from 'vitest'

import type { Tarea } from './api'
import { quedan } from './Tareas'

/** Una tarea con solo lo que la cuenta mira: si está hecha. */
function tarea(hecha: boolean): Tarea {
  return {
    id: 1,
    pieza_id: 1,
    texto: 'Grabar la voz',
    hecha,
    marcada_por: hecha ? 'johan' : null,
    marcada_en: hecha ? '2026-09-25T15:00:00Z' : null,
    creada_por: 'johan',
    creada_en: '2026-09-25T14:00:00Z',
  }
}

describe('AD6: cuántas le quedan, de cuántas', () => {
  it('sin tareas no dice nada', () => {
    expect(quedan([])).toBeNull()
  })

  it('cuenta las pendientes sobre el total', () => {
    expect(quedan([tarea(false), tarea(true), tarea(false)])).toBe('quedan 2 de 3 tareas')
  })

  it('en singular cuando queda una', () => {
    expect(quedan([tarea(false), tarea(true)])).toBe('queda 1 de 2 tareas')
    expect(quedan([tarea(false)])).toBe('queda 1 de 1 tarea')
  })

  it('con todas hechas, lo dice así y no «quedan 0»', () => {
    expect(quedan([tarea(true), tarea(true)])).toBe('2 tareas hechas')
    expect(quedan([tarea(true)])).toBe('1 tarea hecha')
  })
})
