/**
 * El boceto en pantalla (Fase 9, AV): las palabras de sus tipos, el orden en
 * que se leen sus elementos y si se quedó viejo. Puro, con sus pruebas en
 * `boceto.test.ts`.
 */

import type { Boceto, ElementoDelBoceto, Pieza } from './api'

/** Los siete tipos del esquema de la API (`api/app/bocetos.py`), en palabras. */
const TIPOS: Record<string, string> = {
  titulo: 'Título',
  dato: 'Dato',
  texto: 'Texto',
  formula: 'Fórmula',
  figura: 'Figura',
  grafica: 'Gráfica',
  nota: 'Nota',
}

/** Como `enPalabras` de `flujo.ts`: un tipo que no esté aquí se ve tal cual. */
export function palabraDelTipo(tipo: string): string {
  return TIPOS[tipo] ?? tipo
}

/**
 * El orden en que se leen: por peso, y a igual peso, de arriba abajo y de
 * izquierda a derecha. Es el del lector de pantalla, que sigue el DOM; a la
 * vista, la rejilla pone cada uno en su zona sea cual sea su orden.
 */
export function porPeso(elementos: ElementoDelBoceto[]): ElementoDelBoceto[] {
  return [...elementos].sort(
    (a, b) => a.peso - b.peso || a.zona.fila - b.zona.fila || a.zona.col - b.zona.col,
  )
}

/** AV5: el copy gráfico de la pieza ya no es el del boceto. */
export function anticuado(boceto: Boceto, pieza: Pieza): boolean {
  return (
    boceto.copy_grafico.length !== pieza.copy_grafico.length ||
    boceto.copy_grafico.some((lamina, i) => lamina !== pieza.copy_grafico[i])
  )
}

/**
 * Una fórmula del boceto, lista para la vista previa del guion: entre `$`.
 * La API las pide sin ellos, pero si llegan con ellos no se duplican.
 */
export function comoFormula(latex: string): string {
  return `$${latex.trim().replace(/^\$+|\$+$/g, '').trim()}$`
}

/** Las figuras y las gráficas son el hueco de una imagen: llevan el aspa. */
export function esHueco(tipo: string): boolean {
  return tipo === 'figura' || tipo === 'grafica'
}
