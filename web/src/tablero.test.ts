/**
 * Criterios AB1 y AB2 de la Fase 6: el tablero reparte las piezas en una
 * columna por estado.
 */

import { describe, expect, it } from 'vitest'

import type { Pieza } from './api'
import { piezaDePrueba } from './piezaDePrueba'
import { tablero, type Columna } from './tablero'

/** Una pieza con solo lo que el tablero mira: cuál es y en qué estado está. */
function pieza(id: number, estado: string): Pieza {
  return piezaDePrueba({ id, titulo: `Pieza ${id}`, estado, de_quien_es: null })
}

function enColumnas(columnas: Columna[]): [string, number[]][] {
  return columnas.map((c) => [c.estado, c.piezas.map((p) => p.id)])
}

describe('AB1: una columna por estado, en el orden del flujo', () => {
  it('pone las seis columnas aunque no haya piezas', () => {
    expect(tablero([]).map((c) => c.estado)).toEqual([
      'investigacion',
      'solicitud_entregada',
      'material_aprobado',
      'finalizada',
      'diseno_aprobado',
      'publicada',
    ])
  })

  it('cada pieza va a la columna de su estado, en el orden en que llegó', () => {
    const piezas = [pieza(3, 'finalizada'), pieza(2, 'investigacion'), pieza(1, 'finalizada')]

    expect(enColumnas(tablero(piezas))).toEqual([
      ['investigacion', [2]],
      ['solicitud_entregada', []],
      ['material_aprobado', []],
      ['finalizada', [3, 1]],
      ['diseno_aprobado', []],
      ['publicada', []],
    ])
  })
})

describe('AB2: un estado que el cliente no conoce no esconde la pieza', () => {
  it('le abre su propia columna, al final, con su identificador', () => {
    const piezas = [pieza(1, 'en_revision'), pieza(2, 'publicada'), pieza(3, 'en_revision')]
    const columnas = tablero(piezas)

    expect(columnas).toHaveLength(7)
    expect(enColumnas(columnas).at(-1)).toEqual(['en_revision', [1, 3]])
  })
})
