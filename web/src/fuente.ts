/**
 * BC de la Fase 12: qué fuentes son de esta pieza y cuáles solo están en el
 * vault. Funciones puras, para probarlas sin navegador.
 */

import type { NotaDeRespaldo } from './api'

export type Reparto = {
  /** Las enlazadas a la pieza que siguen en el vault, en el orden en que se enlazaron. */
  enlazadas: NotaDeRespaldo[]
  /** Enlazadas cuyo archivo ya no está: renombradas o borradas en Obsidian. */
  perdidas: string[]
  /** Las demás del vault, filtradas por la búsqueda. */
  disponibles: NotaDeRespaldo[]
}

/** Sin mayúsculas ni tildes: «cosmologia» encuentra «Cosmología». */
const llano = (texto: string) =>
  texto
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()

/**
 * La búsqueda solo filtra las disponibles: lo que ya es de la pieza se ve
 * siempre, o buscar escondería qué respalda el guion.
 */
export function repartir(notas: NotaDeRespaldo[], respaldo: string[], busqueda: string): Reparto {
  const porArchivo = new Map(notas.map((nota) => [nota.archivo, nota]))
  const palabras = llano(busqueda).split(/\s+/).filter(Boolean)

  return {
    enlazadas: respaldo.flatMap((archivo) => porArchivo.get(archivo) ?? []),
    perdidas: respaldo.filter((archivo) => !porArchivo.has(archivo)),
    disponibles: notas.filter((nota) => {
      if (respaldo.includes(nota.archivo)) return false
      const donde = llano(`${nota.fuente_titulo} ${nota.archivo} ${nota.autor ?? ''}`)
      return palabras.every((palabra) => donde.includes(palabra))
    }),
  }
}
