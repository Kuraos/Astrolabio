/**
 * Criterios AX6 y AX7 de la Fase 10: dónde se atasca cada pieza, dicho en
 * días y ordenado para verlo de un vistazo.
 */

import { describe, expect, it } from 'vitest'

import type { Atasco } from './api'
import { atascadas, enDias, segundosEn, vueltas } from './atasco'
import { piezaDePrueba } from './piezaDePrueba'

const DIA = 24 * 60 * 60

function atasco(cambios: Partial<Atasco> & { pieza_id: number }): Atasco {
  return {
    etapas: [],
    en_estado: 0,
    ciclo: null,
    devoluciones: 0,
    reformulaciones: 0,
    ...cambios,
  }
}

describe('AX7: los días, en palabras', () => {
  it('menos de un día no se redondea a uno ni se llama «hoy»', () => {
    expect(enDias(0)).toBe('menos de 1 día')
    expect(enDias(DIA - 1)).toBe('menos de 1 día')
  })

  it('cuenta los días enteros que caben', () => {
    expect(enDias(DIA)).toBe('1 día')
    expect(enDias(2 * DIA - 1)).toBe('1 día')
    expect(enDias(12 * DIA + 3600)).toBe('12 días')
  })
})

describe('las vueltas atrás', () => {
  it('nada, si nunca volvió', () => {
    expect(vueltas(atasco({ pieza_id: 1 }))).toBeNull()
  })

  it('devoluciones y reformulaciones, cada una con su número', () => {
    expect(vueltas(atasco({ pieza_id: 1, devoluciones: 1 }))).toBe('1 devolución')
    expect(vueltas(atasco({ pieza_id: 1, devoluciones: 2, reformulaciones: 1 }))).toBe(
      '2 devoluciones · 1 reformulación',
    )
    expect(vueltas(atasco({ pieza_id: 1, reformulaciones: 3 }))).toBe('3 reformulaciones')
  })
})

describe('AX6: en curso y publicadas', () => {
  const piezas = [
    piezaDePrueba({ id: 1, titulo: 'Reciente' }),
    piezaDePrueba({ id: 2, titulo: 'Publicada', estado: 'publicada', de_quien_es: null }),
    piezaDePrueba({ id: 3, titulo: 'Atascada' }),
  ]
  const tiempos = [
    atasco({ pieza_id: 1, en_estado: DIA }),
    atasco({ pieza_id: 2, en_estado: null, ciclo: 8 * DIA }),
    atasco({ pieza_id: 3, en_estado: 9 * DIA }),
  ]

  it('en curso, la que lleva más tiempo donde está primero', () => {
    const { enCurso } = atascadas(piezas, tiempos)

    expect(enCurso.map((fila) => fila.pieza.titulo)).toEqual(['Atascada', 'Reciente'])
  })

  it('las publicadas, aparte y en el orden de la lista', () => {
    const { publicadas } = atascadas(piezas, tiempos)

    expect(publicadas.map((fila) => fila.pieza.titulo)).toEqual(['Publicada'])
  })

  it('solo las piezas que se le pasan: el filtro por etiqueta vale aquí también', () => {
    const { enCurso, publicadas } = atascadas([piezas[0]], tiempos)

    expect(enCurso.map((fila) => fila.pieza.id)).toEqual([1])
    expect(publicadas).toEqual([])
  })

  it('una pieza sin tiempos no rompe nada: se queda fuera', () => {
    const { enCurso } = atascadas([piezaDePrueba({ id: 99 })], tiempos)

    expect(enCurso).toEqual([])
  })
})

describe('segundosEn', () => {
  it('los de la etapa, o 0 si no pasó por ella', () => {
    const suyo = atasco({ pieza_id: 1, etapas: [{ estado: 'finalizada', segundos: 60 }] })

    expect(segundosEn(suyo, 'finalizada')).toBe(60)
    expect(segundosEn(suyo, 'diseno_aprobado')).toBe(0)
  })
})
