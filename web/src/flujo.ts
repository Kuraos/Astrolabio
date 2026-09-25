/**
 * Las palabras del flujo en pantalla (criterio N4).
 *
 * Qué se puede hacer con una pieza lo dice la API (K4); aquí solo se decide
 * cómo se lee. Las palabras son las de `docs/estados-del-flujo.md`, no los
 * identificadores del código.
 */

import type { Pieza, Rol, Usuario } from './api'

const PALABRAS: Record<string, string> = {
  investigacion: 'investigación',
  solicitud_entregada: 'solicitud entregada',
  material_aprobado: 'material aprobado',
  finalizada: 'finalizada',
  diseno_aprobado: 'diseño aprobado',
  publicada: 'publicada',

  entregar: 'Entregar',
  aprobar_material: 'Aprobar el material',
  devolver: 'Devolver',
  finalizar: 'Finalizar',
  aprobar_diseno: 'Aprobar el diseño',
  publicar: 'Publicar',
  reformular: 'Reformular',
}

/** Un identificador que no esté aquí se ve tal cual: feo, pero no invisible. */
export function enPalabras(identificador: string): string {
  return PALABRAS[identificador] ?? identificador
}

/**
 * A quién le toca, dicho desde quien mira. `null` cuando no le toca a nadie:
 * la pieza está publicada, y su estado ya lo dice.
 *
 * «Le toca al editor» solo lo lee Johan. El editor nunca ve esa palabra, que
 * sigue en duda para él (estados §6.6).
 */
export function aQuienLeToca(pieza: Pieza, usuario: Usuario): string | null {
  if (pieza.de_quien_es === null) return null
  if (pieza.de_quien_es === usuario.rol) return 'Te toca'
  return pieza.de_quien_es === 'investigador' ? 'Le toca a Johan' : 'Le toca al editor'
}

/**
 * De quién es cada estado: el mismo `DE_QUIEN_ES` de `api/app/models.py`. El
 * servidor lo dice pieza a pieza, y la franja del tablero lo necesita también
 * en las columnas vacías (AH2). Si cambia allí, cambia aquí.
 */
const DE_QUIEN_ES: Record<string, Rol | null> = {
  investigacion: 'investigador',
  solicitud_entregada: 'investigador',
  material_aprobado: 'editor',
  finalizada: 'investigador',
  diseno_aprobado: 'investigador',
  publicada: null,
}

/**
 * AH2: de quién es un estado, dicho desde quien mira: «tú», o el otro. `null`
 * si no es de nadie o el cliente no lo conoce. Como en `aQuienLeToca`, el
 * editor nunca lee «editor».
 */
export function duenoDelEstado(estado: string, usuario: Usuario): string | null {
  const rol = DE_QUIEN_ES[estado]
  if (!rol) return null
  if (rol === usuario.rol) return 'tú'
  return rol === 'investigador' ? 'Johan' : 'editor'
}

/**
 * Solo para el estilo: las que devuelven la pieza van como botón secundario,
 * después de las que la hacen avanzar. Qué botones aparecen lo decide la API.
 */
const VUELVEN_ATRAS = new Set(['devolver', 'reformular'])

export function vuelveAtras(transicion: string): boolean {
  return VUELVEN_ATRAS.has(transicion)
}

/**
 * Los pasos que no se deshacen con otro clic, con la pregunta que los
 * confirma. De `publicada` no sale nada, y de `diseño aprobado` solo se sale
 * publicando o reformulando desde el principio. Un clic de más en «Aprobar el
 * diseño» ya obligó una vez a rehacer el recorrido entero.
 */
const CONFIRMACIONES: Record<string, string> = {
  aprobar_diseno:
    '¿Aprobar el diseño? Después ya no vuelve al editor: solo queda publicarla o reformularla desde el principio.',
  publicar: '¿Marcar la pieza como publicada? Después ya no se puede mover.',
}

export function confirmacion(transicion: string): string | null {
  return CONFIRMACIONES[transicion] ?? null
}
