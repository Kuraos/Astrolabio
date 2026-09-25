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
