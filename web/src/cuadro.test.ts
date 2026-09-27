/**
 * Criterios AO1, AO2 y AP3 de la Fase 8: el cuadro de materiales en pantalla.
 */

import { describe, expect, it } from 'vitest'

import {
  DESTINOS,
  LIMITES_DEL_CAPTION,
  NIVELES,
  PROPOSITOS,
  TIPOS_DE_PIEZA,
  conCaption,
  esDeUnaLamina,
  faltaDelCuadro,
  palabraDe,
  resumen,
} from './cuadro'
import { piezaDePrueba } from './piezaDePrueba'

/** Una pieza con el cuadro completo, para quitarle una cosa cada vez. */
const completa = piezaDePrueba({
  formato: 'carrusel',
  proposito: 'educar',
  nivel: 'basico',
  plataforma: ['instagram', 'tiktok'],
  copy_grafico: ['La luz que ves salió hace 8 minutos'],
  caption: '¿Lo sabías? #astronomia',
  fecha_entrega: '2026-10-02',
})

describe('AO1: las palabras del editor', () => {
  it('cada identificador tiene su palabra', () => {
    expect(palabraDe('post_individual')).toBe('Post individual')
    expect(palabraDe('poster')).toBe('Póster')
    expect(palabraDe('basico')).toBe('Básico')
    expect(palabraDe('tiktok')).toBe('TikTok')
  })

  it('las listas son las de la API, sin repetir identificadores', () => {
    const valores = [...TIPOS_DE_PIEZA, ...PROPOSITOS, ...NIVELES, ...DESTINOS].map((o) => o.valor)

    expect(new Set(valores).size).toBe(valores.length)
    expect(TIPOS_DE_PIEZA.map((o) => o.valor)).toEqual([
      'carrusel',
      'post_individual',
      'short',
      'poster',
      'video_largo',
    ])
  })

  it('ninguna palabra dice «formato»', () => {
    const todas = [...TIPOS_DE_PIEZA, ...PROPOSITOS, ...NIVELES, ...DESTINOS].map((o) => o.palabra)

    expect(todas.join(' ').toLowerCase()).not.toContain('formato')
  })

  it('el resumen dice qué es, adónde va, para qué, a qué nivel y el tema', () => {
    expect(resumen({ ...completa, tema: 'Sistema Solar' })).toBe(
      'Carrusel · Instagram, TikTok · Educar · Básico · Sistema Solar',
    )
  })

  it('el resumen se salta lo que no hay', () => {
    expect(resumen(piezaDePrueba({ formato: 'short' }))).toBe('Short')
    expect(resumen(piezaDePrueba())).toBe('')
  })
})

describe('AO2: lo que falta del cuadro', () => {
  it('con todo, no falta nada', () => {
    expect(faltaDelCuadro(completa)).toEqual([])
  })

  it('una pieza recién creada lo tiene todo por decidir', () => {
    expect(faltaDelCuadro(piezaDePrueba())).toEqual([
      'tipo de pieza',
      'propósito',
      'nivel',
      'destino',
      'copy gráfico',
      'entrega del diseño',
    ])
  })

  it('un copy gráfico de láminas en blanco sigue faltando', () => {
    expect(faltaDelCuadro({ ...completa, copy_grafico: ['', '  '] })).toEqual(['copy gráfico'])
  })

  it('el caption falta si algún destino es una red', () => {
    expect(faltaDelCuadro({ ...completa, caption: ' ' })).toEqual(['caption'])
  })

  it('un impreso no lleva caption', () => {
    expect(faltaDelCuadro({ ...completa, plataforma: ['impreso'], caption: '' })).toEqual([])
    expect(conCaption(['instagram', 'impreso'])).toEqual(['instagram'])
  })
})

describe('AP2 y AP3', () => {
  it('el post individual y el póster son de una lámina', () => {
    expect(TIPOS_DE_PIEZA.filter((o) => esDeUnaLamina(o.valor)).map((o) => o.valor)).toEqual([
      'post_individual',
      'poster',
    ])
    expect(esDeUnaLamina(null)).toBe(false)
  })

  it('cada destino con caption tiene su fila de límites, y el impreso no', () => {
    expect(Object.keys(LIMITES_DEL_CAPTION).sort()).toEqual(
      conCaption(DESTINOS.map((o) => o.valor)).sort(),
    )
  })
})
