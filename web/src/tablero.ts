import type { Pieza } from './api'

/**
 * Los estados en el orden del flujo, el mismo de `ESTADOS` en
 * `api/app/models.py`. Si el servidor añade uno, sus piezas no desaparecen:
 * salen en su propia columna (AB2).
 */
export const ESTADOS = [
  'investigacion',
  'solicitud_entregada',
  'material_aprobado',
  'finalizada',
  'diseno_aprobado',
  'publicada',
]

export type Columna = { estado: string; piezas: Pieza[] }

/**
 * AB1 y AB2: una columna por estado, en el orden del flujo y aunque esté
 * vacía, y en cada una las piezas en el orden en que llegan de la API.
 *
 * Una pieza con un estado que el cliente no conoce abre su propia columna al
 * final, con su identificador: feo, pero no invisible, como `enPalabras`.
 */
export function tablero(piezas: Pieza[]): Columna[] {
  const columnas = new Map<string, Pieza[]>(ESTADOS.map((estado) => [estado, []]))
  for (const pieza of piezas) {
    const columna = columnas.get(pieza.estado) ?? []
    columna.push(pieza)
    columnas.set(pieza.estado, columna)
  }
  return [...columnas].map(([estado, piezas]) => ({ estado, piezas }))
}
