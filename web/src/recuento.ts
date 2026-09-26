/**
 * AP4: los recuentos del copy gráfico y del caption. Funciones puras, con sus
 * pruebas en `recuento.test.ts`.
 *
 * Los caracteres son los que ve quien escribe —grafemas—, no las unidades de
 * UTF-16 que cuenta `length`: `'☀️'.length` es 2, y una familia de emoji
 * unida con ZWJ pasa de 10. Cómo cuenta cada red un emoji no lo documenta
 * ninguna, así que cerca del límite el recuento es una guía, no el veredicto
 * de la red.
 */

const GRAFEMAS = new Intl.Segmenter('es', { granularity: 'grapheme' })

export function caracteres(texto: string): number {
  let total = 0
  for (const _ of GRAFEMAS.segment(texto)) total++
  return total
}

/** Lo separado por espacios que lleva alguna letra o cifra: un «=» suelto o un emoji no son palabras. */
export function palabras(texto: string): number {
  return texto.split(/\s+/).filter((trozo) => /[\p{L}\p{N}]/u.test(trozo)).length
}

/**
 * Las fórmulas, como las lee `remark-math` en la vista previa: `$$…$$`, o
 * `$…$` dentro de una línea.
 */
const FORMULA = /\$\$[\s\S]+?\$\$|\$[^$\n]+\$/g

export function formulas(texto: string): number {
  return texto.match(FORMULA)?.length ?? 0
}

/**
 * El texto de una lámina sin sus fórmulas, que es lo que se lee como texto:
 * el LaTeX de `$t = d/c \approx 499\,\mathrm{s}$` son 30 caracteres, y en la
 * pieza se ven 11. Las fórmulas se cuentan aparte, y la lámina las enseña
 * pintadas. Sin fórmulas, el texto vuelve tal cual.
 */
export function sinFormulas(texto: string): string {
  if (!formulas(texto)) return texto
  return texto.replace(FORMULA, ' ').replace(/[ \t]{2,}/g, ' ').trim()
}

/**
 * Un `#` seguido de letras, marcas, cifras o `_`, con al menos una letra, y
 * que no va pegado a lo anterior: ni `C#`, ni `&#39;`, ni el `#` de una URL.
 */
const HASHTAG = /(?<![\p{L}\p{M}\p{N}_&/#])#(?=[\p{N}_]*\p{L})[\p{L}\p{M}\p{N}_]+/gu

export function hashtags(texto: string): number {
  return texto.match(HASHTAG)?.length ?? 0
}
