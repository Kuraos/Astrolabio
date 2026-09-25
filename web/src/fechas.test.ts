/**
 * Criterios AC4 y AC5 de la Fase 6: una fecha de calendario se pinta el día
 * que dice.
 */

import { describe, expect, it } from 'vitest'

import { diaYMes } from './fechas'

// El cliente no carga los tipos de Node, y por una línea no vale la pena una
// dependencia: basta con decirle a TypeScript que `process` existe.
declare const process: { env: Record<string, string | undefined> }

// En UTC, `new Date('2026-10-02')` cae el mismo día y el error no se ve, y la
// CI corre en UTC. Estas pruebas se ponen en la zona de Bogotá, donde sí se
// ve: Node cambia de zona al asignar `TZ`, también con el proceso andando.
process.env.TZ = 'America/Bogota'

describe('AC5: AAAA-MM-DD es un día del calendario, no una hora en UTC', () => {
  it('corre en la zona de Bogotá, o no probaría nada', () => {
    // UTC−5 todo el año, sin horario de verano: 300 minutos por detrás.
    expect(new Date(2026, 9, 2).getTimezoneOffset()).toBe(300)
  })

  it('pinta el día que dice, no el anterior', () => {
    expect(diaYMes('2026-10-02')).toBe('2 de oct')
  })

  it('el primero del mes no cae en el mes anterior', () => {
    expect(diaYMes('2026-10-01')).toBe('1 de oct')
  })

  it('ni el primero del año en el año anterior', () => {
    expect(diaYMes('2027-01-01')).toBe('1 de ene')
  })
})
