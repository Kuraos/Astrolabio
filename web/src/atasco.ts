import type { Atasco, Pieza } from './api'

/**
 * Dónde se atasca cada pieza (Fase 10, AX6 y AX7). Los tiempos los calcula la
 * API; aquí solo se juntan con las piezas y se dicen en palabras.
 */

const DIA = 24 * 60 * 60

/**
 * AX7: los días enteros que caben. Menos de uno no es «hoy»: una pieza que
 * llegó anoche lleva menos de un día, pero llegó ayer.
 */
export function enDias(segundos: number): string {
  const dias = Math.floor(segundos / DIA)
  if (dias < 1) return 'menos de 1 día'
  return dias === 1 ? '1 día' : `${dias} días`
}

/** Cuántas veces volvió atrás, o `null` si nunca: nada que decir. */
export function vueltas(atasco: Atasco): string | null {
  const partes = []
  if (atasco.devoluciones > 0) {
    partes.push(
      atasco.devoluciones === 1 ? '1 devolución' : `${atasco.devoluciones} devoluciones`,
    )
  }
  if (atasco.reformulaciones > 0) {
    partes.push(
      atasco.reformulaciones === 1
        ? '1 reformulación'
        : `${atasco.reformulaciones} reformulaciones`,
    )
  }
  return partes.length > 0 ? partes.join(' · ') : null
}

export type Fila = { pieza: Pieza; atasco: Atasco }

/**
 * AX6: las piezas en curso, la que lleva más tiempo donde está primero, y las
 * publicadas, en el orden de la lista. Solo las de `piezas`, que pueden venir
 * filtradas por etiqueta (AB4). Nada de medias ni de totales (decisión 4).
 */
export function atascadas(piezas: Pieza[], atasco: Atasco[]): { enCurso: Fila[]; publicadas: Fila[] } {
  const porPieza = new Map(atasco.map((a) => [a.pieza_id, a]))
  const filas = piezas.flatMap((pieza) => {
    const suyo = porPieza.get(pieza.id)
    return suyo ? [{ pieza, atasco: suyo }] : []
  })

  return {
    enCurso: filas
      .filter((fila) => fila.atasco.en_estado !== null)
      .sort((a, b) => (b.atasco.en_estado ?? 0) - (a.atasco.en_estado ?? 0)),
    publicadas: filas.filter((fila) => fila.atasco.en_estado === null),
  }
}

/** Los segundos de una etapa, o 0 si la pieza no pasó por ella. */
export function segundosEn(atasco: Atasco, estado: string): number {
  return atasco.etapas.find((etapa) => etapa.estado === estado)?.segundos ?? 0
}
