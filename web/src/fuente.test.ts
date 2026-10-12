/** Criterios BC de la Fase 12: las fuentes de la pieza, aparte de las del vault. */

import { describe, expect, it } from 'vitest'

import type { NotaDeRespaldo } from './api'
import { repartir } from './fuente'

const nota = (archivo: string, autor: string | null = null): NotaDeRespaldo => ({
  archivo,
  fuente_titulo: `Título de ${archivo}`,
  fuente_tipo: 'paper',
  autor,
  fecha: null,
})

const NOTAS = [nota('GWTC-5', 'LIGO'), nota('Cosmología de precisión', 'Planck'), nota('Paralaje')]

describe('BC1: lo enlazado, aparte de lo disponible', () => {
  it('separa las de la pieza de las demás', () => {
    const reparto = repartir(NOTAS, ['Paralaje'], '')

    expect(reparto.enlazadas.map((n) => n.archivo)).toEqual(['Paralaje'])
    expect(reparto.disponibles.map((n) => n.archivo)).toEqual(['GWTC-5', 'Cosmología de precisión'])
    expect(reparto.perdidas).toEqual([])
  })

  it('las enlazadas van en el orden en que se enlazaron, no en el del vault', () => {
    const reparto = repartir(NOTAS, ['Paralaje', 'GWTC-5'], '')

    expect(reparto.enlazadas.map((n) => n.archivo)).toEqual(['Paralaje', 'GWTC-5'])
  })

  it('una enlazada que ya no está en el vault se dice, no se esconde', () => {
    const reparto = repartir(NOTAS, ['Renombrada en Obsidian', 'Paralaje'], '')

    expect(reparto.perdidas).toEqual(['Renombrada en Obsidian'])
    expect(reparto.enlazadas.map((n) => n.archivo)).toEqual(['Paralaje'])
  })
})

describe('BC2: buscar entre las disponibles', () => {
  it('por título, por nombre de la nota o por autor, sin tildes ni mayúsculas', () => {
    expect(repartir(NOTAS, [], 'cosmologia').disponibles.map((n) => n.archivo)).toEqual([
      'Cosmología de precisión',
    ])
    expect(repartir(NOTAS, [], 'ligo').disponibles.map((n) => n.archivo)).toEqual(['GWTC-5'])
    expect(repartir(NOTAS, [], 'TÍTULO paralaje').disponibles.map((n) => n.archivo)).toEqual([
      'Paralaje',
    ])
  })

  it('todas las palabras tienen que estar', () => {
    expect(repartir(NOTAS, [], 'cosmologia ligo').disponibles).toEqual([])
  })

  it('no esconde lo que ya es de la pieza', () => {
    const reparto = repartir(NOTAS, ['Paralaje'], 'ligo')

    expect(reparto.enlazadas.map((n) => n.archivo)).toEqual(['Paralaje'])
  })
})
