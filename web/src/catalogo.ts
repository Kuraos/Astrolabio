import type { Pieza } from './api'

/** Una etiqueta del catálogo, con sus piezas publicadas y en curso. */
export type Entrada = { etiqueta: string; publicadas: number; enCurso: number }

/**
 * Z1: cada etiqueta en uso, con cuántas piezas publicadas tiene —de qué hemos
 * hablado— y cuántas en curso —de qué estamos hablando—. Sale de la lista de
 * piezas que la app ya carga, sin endpoint propio.
 *
 * Z3: en orden alfabético del español, con la ñ entre la n y la o, para que
 * no se lea como un ranking (§2.7 de `AGENTS.md`).
 */
export function catalogo(piezas: Pieza[]): Entrada[] {
  const entradas = new Map<string, Entrada>()
  for (const pieza of piezas) {
    for (const etiqueta of pieza.etiquetas) {
      const entrada = entradas.get(etiqueta) ?? { etiqueta, publicadas: 0, enCurso: 0 }
      if (pieza.estado === 'publicada') entrada.publicadas++
      else entrada.enCurso++
      entradas.set(etiqueta, entrada)
    }
  }
  return [...entradas.values()].sort((a, b) => a.etiqueta.localeCompare(b.etiqueta, 'es'))
}
