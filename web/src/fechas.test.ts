/**
 * Criterios AC4, AC5 y AE1 de la Fase 6: una fecha de calendario se pinta el
 * día que dice, y lo pendiente con fecha se agrupa por semanas.
 */

import { describe, expect, it } from 'vitest'

import type { Pieza } from './api'
import { diaDeLaSemana, diaYMes, lunesDe, semanas, type Semana } from './fechas'

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

  it('el día de la semana tampoco se corre', () => {
    // El 28 de septiembre de 2026 es lunes; leído en UTC desde Bogotá, domingo.
    expect(diaDeLaSemana('2026-09-28')).toBe('lun 28')
  })
})

describe('AE1: la semana va de lunes a domingo (§7.6)', () => {
  it('un lunes empieza su propia semana', () => {
    expect(lunesDe('2026-09-28')).toBe('2026-09-28')
  })

  it('el domingo cierra la del lunes anterior, no abre la siguiente', () => {
    expect(lunesDe('2026-10-04')).toBe('2026-09-28')
  })

  it('cruza de mes y de año sin correrse', () => {
    expect(lunesDe('2027-01-01')).toBe('2026-12-28')
  })
})

/** Una pieza con solo lo que las semanas miran: su estado y sus fechas. */
function pieza(
  id: number,
  estado: string,
  fechas: { fecha_entrega?: string; fecha_publicacion_prevista?: string },
): Pieza {
  return {
    id,
    titulo: `Pieza ${id}`,
    creada_en: '2026-09-01T00:00:00Z',
    creada_por: 'johan',
    guion: '',
    formato: null,
    tema: null,
    plataforma: null,
    respaldo: [],
    etiquetas: [],
    fecha_entrega: fechas.fecha_entrega ?? null,
    fecha_publicacion_prevista: fechas.fecha_publicacion_prevista ?? null,
    estado,
    de_quien_es: null,
    transiciones: [],
  }
}

function entradas(lista: Semana[]): [string, string, number][] {
  return lista.flatMap((s) => s.entradas.map((e): [string, string, number] => [e.fecha, e.tipo, e.pieza.id]))
}

// Un viernes: su semana empezó el lunes 21.
const HOY = '2026-09-25'

describe('AE1: lo que sigue pendiente, por semanas', () => {
  it('la entrega cuenta hasta que el editor finaliza la pieza', () => {
    const piezas = [
      pieza(1, 'material_aprobado', { fecha_entrega: '2026-09-29' }),
      pieza(2, 'finalizada', { fecha_entrega: '2026-09-30' }),
      pieza(3, 'publicada', { fecha_entrega: '2026-10-01' }),
    ]

    expect(entradas(semanas(piezas, HOY))).toEqual([['2026-09-29', 'entrega', 1]])
  })

  it('la publicación prevista cuenta hasta que se publica', () => {
    const piezas = [
      pieza(1, 'diseno_aprobado', { fecha_publicacion_prevista: '2026-10-02' }),
      pieza(2, 'publicada', { fecha_publicacion_prevista: '2026-10-01' }),
    ]

    expect(entradas(semanas(piezas, HOY))).toEqual([['2026-10-02', 'publicacion', 1]])
  })

  it('agrupa por semana, en orden, y dentro de cada una por fecha', () => {
    const piezas = [
      pieza(1, 'investigacion', {
        fecha_entrega: '2026-10-08',
        fecha_publicacion_prevista: '2026-09-30',
      }),
      pieza(2, 'solicitud_entregada', { fecha_entrega: '2026-09-29' }),
    ]

    expect(semanas(piezas, HOY).map((s) => [s.lunes, s.entradas.map((e) => e.fecha)])).toEqual([
      ['2026-09-28', ['2026-09-29', '2026-09-30']],
      ['2026-10-05', ['2026-10-08']],
    ])
  })

  it('señala la semana en curso, y lo de antes sale primero: es lo atrasado', () => {
    const piezas = [
      pieza(1, 'material_aprobado', { fecha_entrega: '2026-09-30' }),
      pieza(2, 'material_aprobado', { fecha_entrega: '2026-09-23' }),
      pieza(3, 'material_aprobado', { fecha_entrega: '2026-09-14' }),
    ]

    expect(semanas(piezas, HOY).map((s) => [s.lunes, s.cuando])).toEqual([
      ['2026-09-14', 'pasada'],
      ['2026-09-21', 'esta'],
      ['2026-09-28', 'futura'],
    ])
  })

  it('sin fechas pendientes no hay semanas', () => {
    expect(semanas([pieza(1, 'investigacion', {})], HOY)).toEqual([])
  })
})
