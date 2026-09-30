/**
 * El aviso de «te toca» (Fase 10, AZ): el título de la pestaña dice cuántas
 * piezas te tocan, y la lista se recarga sola mientras la pestaña se ve.
 *
 * Solo funciona con la pestaña abierta (AZ5): nada sale de la app, ni correo
 * ni notificaciones (decisión 6). Si en el uso no alcanza, el paso siguiente
 * es un servicio externo con su ADR.
 */

const MARCA = 'Astrolabio'

/** AZ1: `(N) Astrolabio`, o la marca a secas cuando no te toca nada. */
export function tituloDeLaPestana(cuantas: number): string {
  return cuantas > 0 ? `(${cuantas}) ${MARCA}` : MARCA
}

/** Cada cuánto se recarga la lista mientras la pestaña se ve (AZ2). */
export const CADA = 60_000

/** Lo que se mira del documento: `document` lo cumple, y una prueba, sin navegador. */
type Pagina = EventTarget & { visibilityState: DocumentVisibilityState }

/**
 * AZ2: llama a `recargar` cuando la pestaña vuelve a verse y cada minuto
 * mientras se ve. Oculta, no hace nada: ni un pedido. Devuelve cómo dejar de
 * vigilar.
 */
export function recargarMientrasSeVe(recargar: () => void, pagina: Pagina = document): () => void {
  const siSeVe = () => {
    if (pagina.visibilityState === 'visible') recargar()
  }
  const reloj = setInterval(siSeVe, CADA)
  pagina.addEventListener('visibilitychange', siSeVe)

  return () => {
    clearInterval(reloj)
    pagina.removeEventListener('visibilitychange', siSeVe)
  }
}
