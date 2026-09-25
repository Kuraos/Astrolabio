/**
 * Criterios Z1 y Z3 de la Fase 5: el catálogo de etiquetas, que sale de la
 * lista de piezas que ya carga la app.
 */

import { describe, expect, it } from 'vitest'

import type { Pieza } from './api'
import { catalogo } from './catalogo'

/** Una pieza con solo lo que el catálogo mira: su estado y sus etiquetas. */
function pieza(estado: string, etiquetas: string[]): Pieza {
  return {
    id: 1,
    titulo: 'Una pieza',
    creada_en: '2026-09-24T00:00:00Z',
    creada_por: 'johan',
    guion: '',
    formato: null,
    tema: null,
    plataforma: null,
    respaldo: [],
    etiquetas,
    estado,
    de_quien_es: null,
    transiciones: [],
  }
}

describe('Z1: cada etiqueta, con sus piezas publicadas y en curso', () => {
  it('cuenta las publicadas y las que siguen en curso', () => {
    const piezas = [
      pieza('publicada', ['m31', 'galaxias']),
      pieza('investigacion', ['galaxias']),
      pieza('material_aprobado', ['m31']),
      pieza('publicada', ['galaxias']),
    ]

    expect(catalogo(piezas)).toEqual([
      { etiqueta: 'galaxias', publicadas: 2, enCurso: 1 },
      { etiqueta: 'm31', publicadas: 1, enCurso: 1 },
    ])
  })

  it('una pieza sin etiquetas no aparece', () => {
    expect(catalogo([pieza('publicada', [])])).toEqual([])
  })
})

describe('Z3: en orden alfabético, no como un ranking', () => {
  it('ordena por la etiqueta, no por cuántas piezas tiene', () => {
    const piezas = [
      pieza('publicada', ['via-lactea']),
      pieza('publicada', ['via-lactea']),
      pieza('publicada', ['agujeros-negros']),
    ]

    expect(catalogo(piezas).map((e) => e.etiqueta)).toEqual(['agujeros-negros', 'via-lactea'])
  })

  it('pone la ñ entre la n y la o, como el español', () => {
    // Por código de carácter, la ñ va después de la o y «caos» saldría antes.
    const piezas = [pieza('publicada', ['caos']), pieza('publicada', ['cañones-de-marte'])]

    expect(catalogo(piezas).map((e) => e.etiqueta)).toEqual(['cañones-de-marte', 'caos'])
  })
})
