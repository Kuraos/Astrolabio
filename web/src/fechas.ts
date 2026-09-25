import type { Pieza } from './api'

/**
 * Fechas de calendario, `AAAA-MM-DD`, como las guarda la API (AC1): un día,
 * sin hora ni zona.
 *
 * Nunca pasan por `new Date(texto)`, que las lee como la medianoche UTC: en
 * Bogotá eso son las 19:00 del día anterior, y se pintarían un día antes
 * (AC5). Aquí se construyen en UTC y se formatean en UTC, así que el día no se
 * mueve esté donde esté el navegador.
 */

function enUtc(fecha: string): Date {
  const [anio, mes, dia] = fecha.split('-').map(Number)
  return new Date(Date.UTC(anio, mes - 1, dia))
}

/** AC4: «2 de oct», en `es-CO` como el resto de la app. */
export function diaYMes(fecha: string): string {
  return enUtc(fecha).toLocaleDateString('es-CO', {
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  })
}

/** AE2: «lun 28». */
export function diaDeLaSemana(fecha: string): string {
  return enUtc(fecha).toLocaleDateString('es-CO', {
    weekday: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
}

/** Hoy como día del calendario, en la zona de quien mira. */
export function diaDeHoy(): string {
  const ahora = new Date()
  return [ahora.getFullYear(), ahora.getMonth() + 1, ahora.getDate()]
    .map((n) => String(n).padStart(2, '0'))
    .join('-')
}

/** El lunes de la semana de `fecha`: va de lunes a domingo (Fase 6, §7.6). */
export function lunesDe(fecha: string): string {
  const dia = enUtc(fecha)
  // `getUTCDay` cuenta desde el domingo, que es 0.
  dia.setUTCDate(dia.getUTCDate() - ((dia.getUTCDay() + 6) % 7))
  return dia.toISOString().slice(0, 10)
}

export type Entrada = { fecha: string; tipo: 'entrega' | 'publicacion'; pieza: Pieza }

export type Semana = {
  lunes: string
  cuando: 'pasada' | 'esta' | 'futura'
  entradas: Entrada[]
}

// Después de `finalizada` el editor ya entregó. Un estado que el cliente no
// conozca no suma entregas: se ve en el tablero (AB2), no aquí.
const SIN_ENTREGAR = new Set(['investigacion', 'solicitud_entregada', 'material_aprobado'])

/**
 * AE1: lo que sigue pendiente con fecha, por semanas y en orden: la entrega
 * de cada pieza que el editor aún no ha finalizado, y la publicación prevista
 * de cada una sin publicar. Las semanas anteriores a la de `hoy` son lo
 * atrasado, y salen primero.
 */
export function semanas(piezas: Pieza[], hoy: string): Semana[] {
  const entradas: Entrada[] = []
  for (const pieza of piezas) {
    if (pieza.fecha_entrega && SIN_ENTREGAR.has(pieza.estado)) {
      entradas.push({ fecha: pieza.fecha_entrega, tipo: 'entrega', pieza })
    }
    if (pieza.fecha_publicacion_prevista && pieza.estado !== 'publicada') {
      entradas.push({ fecha: pieza.fecha_publicacion_prevista, tipo: 'publicacion', pieza })
    }
  }
  // `AAAA-MM-DD` ordena como texto igual que como fecha.
  entradas.sort((a, b) => (a.fecha < b.fecha ? -1 : a.fecha > b.fecha ? 1 : 0))

  const porLunes = new Map<string, Entrada[]>()
  for (const entrada of entradas) {
    const lunes = lunesDe(entrada.fecha)
    porLunes.set(lunes, [...(porLunes.get(lunes) ?? []), entrada])
  }

  const estaSemana = lunesDe(hoy)
  return [...porLunes].map(([lunes, suyas]) => ({
    lunes,
    cuando: lunes < estaSemana ? 'pasada' : lunes === estaSemana ? 'esta' : 'futura',
    entradas: suyas,
  }))
}
