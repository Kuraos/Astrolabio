/**
 * Criterio AH2 de la Fase 7: la franja del tablero dice de quién es cada
 * estado desde quien mira, y el editor nunca lee «editor» (estados §6.6).
 */

import { expect, it } from 'vitest'

import type { Usuario } from './api'
import { duenoDelEstado } from './flujo'

const JOHAN: Usuario = { usuario: 'johan', rol: 'investigador' }
const EDITOR: Usuario = { usuario: 'dathzon', rol: 'editor' }

it('a cada uno le dice «tú» en sus estados', () => {
  expect(duenoDelEstado('investigacion', JOHAN)).toBe('tú')
  expect(duenoDelEstado('material_aprobado', EDITOR)).toBe('tú')
})

it('los del otro llevan su nombre, y el editor no lee «editor»', () => {
  expect(duenoDelEstado('material_aprobado', JOHAN)).toBe('editor')
  expect(duenoDelEstado('finalizada', EDITOR)).toBe('Johan')
})

it('publicada no es de nadie, y un estado desconocido tampoco', () => {
  expect(duenoDelEstado('publicada', JOHAN)).toBeNull()
  expect(duenoDelEstado('en_revision', EDITOR)).toBeNull()
})
