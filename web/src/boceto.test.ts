/**
 * Criterios AV2 y AV5 de la Fase 9: lo puro del boceto en pantalla.
 */

import { describe, expect, it } from 'vitest'

import type { Boceto, ElementoDelBoceto } from './api'
import { anticuado, comoFormula, esHueco, palabraDelTipo, porPeso } from './boceto'
import { piezaDePrueba } from './piezaDePrueba'

const elemento = (peso: 1 | 2 | 3 | 4, fila: number, col: number): ElementoDelBoceto => ({
  tipo: 'texto',
  peso,
  contenido: `${peso}-${fila}-${col}`,
  zona: { fila, col, filas: 1, cols: 1 },
})

const boceto = (copy: string[]): Boceto => ({
  id: 1,
  creado_por: 'dathzon',
  creado_en: '2026-09-26T15:00:00Z',
  modelo: 'claude-opus-5',
  columnas: 12,
  filas: 15,
  copy_grafico: copy,
  laminas: [],
  avisos: [],
  tokens_entrada: 2100,
  tokens_salida: 2800,
})

describe('porPeso: el orden de lectura', () => {
  it('primero el peso, después de arriba abajo y de izquierda a derecha', () => {
    const orden = porPeso([elemento(3, 1, 1), elemento(1, 9, 1), elemento(2, 5, 7), elemento(2, 5, 2)])

    expect(orden.map((e) => e.contenido)).toEqual(['1-9-1', '2-5-2', '2-5-7', '3-1-1'])
  })

  it('no cambia la lista que recibe', () => {
    const lista = [elemento(2, 1, 1), elemento(1, 1, 1)]

    porPeso(lista)

    expect(lista[0].peso).toBe(2)
  })
})

describe('anticuado: AV5', () => {
  it('con el mismo copy, no', () => {
    expect(anticuado(boceto(['a', 'b']), piezaDePrueba({ copy_grafico: ['a', 'b'] }))).toBe(false)
  })

  it('con una lámina cambiada, de más o de menos, sí', () => {
    expect(anticuado(boceto(['a', 'b']), piezaDePrueba({ copy_grafico: ['a', 'c'] }))).toBe(true)
    expect(anticuado(boceto(['a']), piezaDePrueba({ copy_grafico: ['a', 'b'] }))).toBe(true)
    expect(anticuado(boceto(['a', 'b']), piezaDePrueba({ copy_grafico: ['a'] }))).toBe(true)
  })
})

describe('comoFormula', () => {
  it('pone la fórmula entre $ para la vista previa', () => {
    expect(comoFormula('t = d/c')).toBe('$t = d/c$')
  })

  it('no los duplica si el modelo ya los puso', () => {
    expect(comoFormula(' $$t = d/c$$ ')).toBe('$t = d/c$')
  })
})

describe('los tipos', () => {
  it('se leen en palabras, y uno desconocido tal cual', () => {
    expect(palabraDelTipo('grafica')).toBe('Gráfica')
    expect(palabraDelTipo('formula')).toBe('Fórmula')
    expect(palabraDelTipo('diagrama')).toBe('diagrama')
  })

  it('las figuras y las gráficas son huecos de imagen', () => {
    expect(['figura', 'grafica', 'titulo', 'formula'].map(esHueco)).toEqual([true, true, false, false])
  })
})
