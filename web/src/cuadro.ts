/**
 * El cuadro de materiales del editor en pantalla (Fase 8, AO y AP).
 *
 * Sus palabras, con mayúscula inicial porque son rótulos, y los
 * identificadores que guardan la base y el vault (ADR 0015). Son las mismas
 * listas que acepta la API (`api/app/piezas.py`): si cambian allí, cambian
 * aquí; si no, la API responde 422 y lo delata, como con `TEMAS`.
 */

import type { Pieza } from './api'

export type Opcion = { valor: string; palabra: string }

/** AN1: el «tipo de pieza», que el código llama `formato` desde la Fase 1. */
export const TIPOS_DE_PIEZA: Opcion[] = [
  { valor: 'carrusel', palabra: 'Carrusel' },
  { valor: 'post_individual', palabra: 'Post individual' },
  { valor: 'short', palabra: 'Short' },
  { valor: 'poster', palabra: 'Póster' },
  { valor: 'video_largo', palabra: 'Video largo' },
]

export const PROPOSITOS: Opcion[] = [
  { valor: 'divulgar', palabra: 'Divulgar' },
  { valor: 'promocionar', palabra: 'Promocionar' },
  { valor: 'educar', palabra: 'Educar' },
  { valor: 'noticia', palabra: 'Noticia' },
  { valor: 'comunidad', palabra: 'Comunidad' },
]

export const NIVELES: Opcion[] = [
  { valor: 'basico', palabra: 'Básico' },
  { valor: 'avanzado', palabra: 'Avanzado' },
]

/** AN4: el «destino». Una pieza puede tener varios: lo de TikTok va tal cual a Instagram. */
export const DESTINOS: Opcion[] = [
  { valor: 'instagram', palabra: 'Instagram' },
  { valor: 'tiktok', palabra: 'TikTok' },
  { valor: 'youtube', palabra: 'YouTube' },
  { valor: 'impreso', palabra: 'Impreso' },
]

const PALABRAS = new Map(
  [...TIPOS_DE_PIEZA, ...PROPOSITOS, ...NIVELES, ...DESTINOS].map((o) => [o.valor, o.palabra]),
)

/** Como `enPalabras` de `flujo.ts`: un identificador que no esté aquí se ve tal cual. */
export function palabraDe(valor: string): string {
  return PALABRAS.get(valor) ?? valor
}

/** AP2: un post individual y un póster son una lámina, y su copy empieza con un campo. */
export function esDeUnaLamina(formato: string | null): boolean {
  return formato === 'post_individual' || formato === 'poster'
}

/** La línea bajo el título de la pieza: qué es, adónde va, para qué, a qué nivel y de qué tema. */
export function resumen(pieza: Pieza): string {
  return [
    pieza.formato && palabraDe(pieza.formato),
    pieza.plataforma.map(palabraDe).join(', '),
    pieza.proposito && palabraDe(pieza.proposito),
    pieza.nivel && palabraDe(pieza.nivel),
    pieza.tema,
  ]
    .filter(Boolean)
    .join(' · ')
}

/** Los destinos que llevan caption: todos menos el impreso. */
export function conCaption(destinos: string[]): string[] {
  return destinos.filter((destino) => destino !== 'impreso')
}

/**
 * AO2: lo que le falta a la pieza de lo que pide el cuadro del editor, en
 * minúscula para ir a media frase. Informa y no bloquea, como la checklist
 * (AD7). La fecha es la entrega del diseño: el cuadro pide «fecha», y el
 * editor trabaja contra ese plazo. El caption solo falta si algún destino lo
 * lleva.
 */
export function faltaDelCuadro(pieza: Pieza): string[] {
  const falta: [boolean, string][] = [
    [!pieza.formato, 'tipo de pieza'],
    [!pieza.proposito, 'propósito'],
    [!pieza.nivel, 'nivel'],
    [pieza.plataforma.length === 0, 'destino'],
    [!pieza.copy_grafico.some((lamina) => lamina.trim()), 'copy gráfico'],
    [conCaption(pieza.plataforma).length > 0 && !pieza.caption.trim(), 'caption'],
    [!pieza.fecha_entrega, 'entrega del diseño'],
  ]
  return falta.filter(([falta]) => falta).map(([, que]) => que)
}

/** `donde`, si el caption no va en el pie de la publicación. */
export type Limite = { caracteres: number | null; hashtags: number | null; donde?: string }

/**
 * AP3: los límites del caption por destino, comprobados el 2026-09-26 y no de
 * memoria (fase 8, §8.3). `null` es que no se pudo comprobar, y entonces se
 * muestra el recuento sin límite. Cambian —Instagram pasó de 30 hashtags a 5
 * en diciembre de 2025—: si algo no cuadra con lo que dice la red, se vuelven
 * a mirar.
 *
 * - Instagram: 2.200 caracteres, y 5 hashtags por publicación o reel desde
 *   diciembre de 2025, anunciado por su cuenta @creators.
 * - TikTok: 4.000 caracteres desde 2023. Del máximo de hashtags, las fuentes
 *   se contradicen.
 * - YouTube: la descripción, 5.000 caracteres; con más de 60 hashtags los
 *   ignora todos, según su ayuda.
 *
 * El impreso no lleva caption.
 */
export const LIMITES_DEL_CAPTION: Record<string, Limite> = {
  instagram: { caracteres: 2200, hashtags: 5 },
  tiktok: { caracteres: 4000, hashtags: null },
  youtube: { caracteres: 5000, hashtags: 60, donde: 'En la descripción' },
}
