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

export type Entrada = {
  fecha: string
  tipo: 'entrega' | 'publicacion'
  pieza: Pieza
  /** Su fecha es anterior a hoy. Lo que vence hoy aún está a tiempo. */
  vencida: boolean
}

export type Semana = {
  lunes: string
  cuando: 'pasada' | 'esta' | 'futura'
  entradas: Entrada[]
}

// Después de `finalizada` el editor ya entregó. Un estado que el cliente no
// conozca no suma entregas: se ve en el tablero (AB2), no aquí.
const SIN_ENTREGAR = new Set(['investigacion', 'solicitud_entregada', 'material_aprobado'])

/** Si el editor aún no ha entregado el diseño: las semanas y la tarjeta. */
export function entregaPendiente(pieza: Pieza): boolean {
  return SIN_ENTREGAR.has(pieza.estado)
}

/**
 * AE1: lo que sigue pendiente con fecha, por semanas y en orden: la entrega
 * de cada pieza que el editor aún no ha finalizado, y la publicación prevista
 * de cada una sin publicar. Las semanas anteriores a la de `hoy` salen
 * primero. Lo atrasado se cuenta por día, como en la tarjeta, y no por
 * semana: una entrega del martes ya está vencida el viernes.
 */
export function semanas(piezas: Pieza[], hoy: string): Semana[] {
  const entradas: Entrada[] = []
  const anotar = (fecha: string, tipo: Entrada['tipo'], pieza: Pieza) =>
    entradas.push({ fecha, tipo, pieza, vencida: fecha < hoy })
  for (const pieza of piezas) {
    if (pieza.fecha_entrega && entregaPendiente(pieza)) {
      anotar(pieza.fecha_entrega, 'entrega', pieza)
    }
    if (pieza.fecha_publicacion_prevista && pieza.estado !== 'publicada') {
      anotar(pieza.fecha_publicacion_prevista, 'publicacion', pieza)
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

/** `fecha` más `dias` días del calendario. */
function masDias(fecha: string, dias: number): string {
  const dia = enUtc(fecha)
  dia.setUTCDate(dia.getUTCDate() + dias)
  return dia.toISOString().slice(0, 10)
}

/** Una columna de la línea: un día, o el salto entre dos semanas lejanas. */
export type Celda = { tipo: 'dia'; fecha: string; hoy: boolean } | { tipo: 'salto' }

/**
 * Una entrada en la línea: de qué columna a qué columna va su etiqueta, en qué
 * carril, y si su día es el principio de la etiqueta o, al final de la línea,
 * su fin. Las columnas cuentan desde 1, como las de una rejilla de CSS.
 */
export type Marca = {
  entrada: Entrada
  cuando: Semana['cuando']
  desde: number
  hasta: number
  ancla: 'inicio' | 'fin'
  carril: number
}

export type Linea = {
  celdas: Celda[]
  semanas: { lunes: string; cuando: Semana['cuando']; desde: number }[]
  marcas: Marca[]
}

/**
 * AI1: las semanas de `semanas()`, en una línea de días. La semana de hoy
 * entra siempre, aunque esté vacía, para saber dónde se está; las que no
 * tienen nada entre dos que sí tienen se dibujan como un salto, no como siete
 * días vacíos. Cada etiqueta ocupa una quinta parte de los días y va al
 * primer carril donde no pisa a otra.
 */
export function lineaDeTiempo(lista: Semana[], hoy: string): Linea {
  if (lista.length === 0) return { celdas: [], semanas: [], marcas: [] }

  const estaSemana = lunesDe(hoy)
  const todas = lista.some((s) => s.lunes === estaSemana)
    ? lista
    : [...lista, { lunes: estaSemana, cuando: 'esta' as const, entradas: [] }].sort((a, b) =>
        a.lunes < b.lunes ? -1 : 1,
      )

  const celdas: Celda[] = []
  const columnaDe = new Map<string, number>()
  const semanasEnLinea: Linea['semanas'] = []
  todas.forEach((semana, i) => {
    if (i > 0 && masDias(todas[i - 1].lunes, 7) !== semana.lunes) celdas.push({ tipo: 'salto' })
    semanasEnLinea.push({ lunes: semana.lunes, cuando: semana.cuando, desde: celdas.length + 1 })
    for (let d = 0; d < 7; d++) {
      const fecha = masDias(semana.lunes, d)
      celdas.push({ tipo: 'dia', fecha, hoy: fecha === hoy })
      columnaDe.set(fecha, celdas.length)
    }
  })

  const dias = celdas.filter((c) => c.tipo === 'dia').length
  const ancho = Math.max(1, Math.round(dias / 5))
  const finDeCarril: number[] = []
  const marcas = todas
    .flatMap((s) => s.entradas.map((entrada) => ({ entrada, cuando: s.cuando })))
    .map(({ entrada, cuando }): Omit<Marca, 'carril'> => {
      const columna = columnaDe.get(entrada.fecha) ?? 1
      // Si no cabe hacia la derecha, la etiqueta acaba en su día.
      return columna + ancho - 1 <= celdas.length
        ? { entrada, cuando, desde: columna, hasta: columna + ancho - 1, ancla: 'inicio' }
        : { entrada, cuando, desde: Math.max(1, columna - ancho + 1), hasta: columna, ancla: 'fin' }
    })
    .sort((a, b) => a.desde - b.desde)
    .map((marca) => {
      let carril = finDeCarril.findIndex((fin) => fin < marca.desde)
      if (carril === -1) carril = finDeCarril.length
      finDeCarril[carril] = marca.hasta
      return { ...marca, carril }
    })

  return { celdas, semanas: semanasEnLinea, marcas }
}
