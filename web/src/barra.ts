/**
 * Las acciones de la barra del guion (criterios T2–T5 y U5 de la Fase 4).
 *
 * Son funciones puras: reciben el texto y la selección, y devuelven un
 * `Cambio`, el tramo que hay que sustituir y dónde queda la selección. No
 * tocan el campo: la vista aplica el cambio con `execCommand('insertText')`,
 * que es lo que conserva el deshacer del navegador (§3 del alcance).
 */

/** Como `selectionStart` y `selectionEnd` del campo. */
export type Seleccion = { inicio: number; fin: number }

/** Sustituir `[desde, hasta)` por `texto` y dejar seleccionado `seleccion`. */
export type Cambio = { desde: number; hasta: number; texto: string; seleccion: Seleccion }

/**
 * Una marca que envuelve, y cuándo se considera que ya está puesta según
 * cuántas veces se repite su carácter a cada lado. Hay que contarlas: `**x**`
 * empieza por `*` y no está en cursiva, y `***x***` tiene las dos.
 */
type Marca = { marca: string; puesta: (antes: number, despues: number) => boolean }

const NEGRITA: Marca = { marca: '**', puesta: (a, d) => a >= 2 && d >= 2 }
const CURSIVA: Marca = { marca: '*', puesta: (a, d) => a % 2 === 1 && d % 2 === 1 }
const FORMULA: Marca = { marca: '$', puesta: (a, d) => a === 1 && d === 1 }

/** Cuántas veces seguidas aparece `c` desde `i`, avanzando en `paso`. */
function racha(texto: string, c: string, i: number, paso: 1 | -1): number {
  let n = 0
  for (; i >= 0 && i < texto.length && texto[i] === c; i += paso) n++
  return n
}

function envolver({ marca, puesta }: Marca, texto: string, { inicio, fin }: Seleccion): Cambio {
  const c = marca[0]
  const k = marca.length
  const dentro = texto.slice(inicio, fin)

  // La selección incluye las marcas: «**hola**».
  const alPrincipio = racha(dentro, c, 0, 1)
  const alFinal = racha(dentro, c, dentro.length - 1, -1)
  if (dentro.length >= 2 * k && puesta(alPrincipio, alFinal)) {
    const limpio = dentro.slice(k, -k)
    return {
      desde: inicio,
      hasta: fin,
      texto: limpio,
      seleccion: { inicio, fin: inicio + limpio.length },
    }
  }

  // Las marcas están justo fuera: **«hola»**, o el par vacío de pulsar dos
  // veces sin escribir, **‸**.
  if (puesta(racha(texto, c, inicio - 1, -1), racha(texto, c, fin, 1))) {
    return {
      desde: inicio - k,
      hasta: fin + k,
      texto: dentro,
      seleccion: { inicio: inicio - k, fin: fin - k },
    }
  }

  return {
    desde: inicio,
    hasta: fin,
    texto: marca + dentro + marca,
    seleccion: { inicio: inicio + k, fin: fin + k },
  }
}

export const negrita = (texto: string, s: Seleccion) => envolver(NEGRITA, texto, s)
export const cursiva = (texto: string, s: Seleccion) => envolver(CURSIVA, texto, s)
export const formulaEnLinea = (texto: string, s: Seleccion) => envolver(FORMULA, texto, s)

/**
 * T3: la selección —o una palabra de relleno— como texto, y `url`
 * seleccionado para pegar encima la dirección.
 */
function conUrl(
  prefijo: string,
  relleno: string,
  texto: string,
  { inicio, fin }: Seleccion,
): Cambio {
  const nuevo = `${prefijo}[${texto.slice(inicio, fin) || relleno}](url)`
  const url = inicio + nuevo.length - 'url)'.length
  return { desde: inicio, hasta: fin, texto: nuevo, seleccion: { inicio: url, fin: url + 3 } }
}

export const enlace = (texto: string, s: Seleccion) => conUrl('', 'enlace', texto, s)
export const imagen = (texto: string, s: Seleccion) => conUrl('!', 'descripción', texto, s)

/**
 * T4: aplica `transformar` a las líneas enteras que toca la selección. Sin
 * selección, deja el cursor al final de la línea, que es donde se sigue
 * escribiendo; con ella, selecciona el bloque entero.
 */
function lineas(
  texto: string,
  { inicio, fin }: Seleccion,
  transformar: (ls: string[]) => string[],
): Cambio {
  // `lastIndexOf` con -1 mira la posición 0: sin esta guarda, un guion que
  // empieza con un salto de línea perdería la primera.
  const desde = inicio === 0 ? 0 : texto.lastIndexOf('\n', inicio - 1) + 1
  // Una selección que acaba justo al empezar una línea no la incluye.
  const ultimo = fin > inicio && texto[fin - 1] === '\n' ? fin - 1 : fin
  const salto = texto.indexOf('\n', ultimo)
  const hasta = salto === -1 ? texto.length : salto

  const nuevo = transformar(texto.slice(desde, hasta).split('\n')).join('\n')
  const final = desde + nuevo.length
  const seleccion = inicio === fin ? { inicio: final, fin: final } : { inicio: desde, fin: final }
  return { desde, hasta, texto: nuevo, seleccion }
}

/**
 * Pone `prefijo` en cada línea con texto, sustituyendo lo que `previo`
 * reconozca como uno de su clase; si todas lo tienen ya, se lo quita. Las
 * líneas vacías de un bloque se respetan, pero una línea vacía sola lo
 * recibe: es donde se empieza a escribir.
 */
function alternar(prefijo: string, previo: RegExp) {
  return (ls: string[]) => {
    const vacia = (l: string) => ls.length > 1 && l.trim() === ''
    const todas = ls.every((l) => vacia(l) || l.startsWith(prefijo))
    return ls.map((l) =>
      vacia(l) ? l : todas ? l.slice(prefijo.length) : prefijo + l.replace(previo, ''),
    )
  }
}

// Nivel 3: en la nota del vault el guion va bajo `## Guion`, y un `##`
// dentro partiría la plantilla en secciones que no son suyas.
export const titulo = (texto: string, s: Seleccion) =>
  lineas(texto, s, alternar('### ', /^#{1,6}\s+/))
export const lista = (texto: string, s: Seleccion) => lineas(texto, s, alternar('- ', /^- /))
export const cita = (texto: string, s: Seleccion) => lineas(texto, s, alternar('> ', /^> /))

/**
 * T5: sustituye `[desde, hasta)` por `contenido` en líneas propias, con una
 * línea en blanco antes y otra después, que es lo que el markdown necesita
 * para reconocer una tabla o una fórmula en bloque. Solo añade las que
 * falten, y ninguna al principio o al final del guion. `dentro` es la
 * selección que queda, contada desde el principio de `contenido`.
 */
function bloque(
  texto: string,
  desde: number,
  hasta: number,
  contenido: string,
  dentro: Seleccion,
): Cambio {
  const antes = texto.slice(0, desde)
  const despues = texto.slice(hasta)
  const arriba =
    antes === '' || antes.endsWith('\n\n') ? '' : antes.endsWith('\n') ? '\n' : '\n\n'
  const abajo =
    despues === '' || despues.startsWith('\n\n') ? '' : despues.startsWith('\n') ? '\n' : '\n\n'
  const base = desde + arriba.length
  return {
    desde,
    hasta,
    texto: arriba + contenido + abajo,
    seleccion: { inicio: base + dentro.inicio, fin: base + dentro.fin },
  }
}

const TABLA = '| Encabezado | Encabezado |\n| --- | --- |\n| Celda | Celda |'

/** Después de la selección, sin borrarla, y con el primer encabezado seleccionado. */
export const tabla = (texto: string, { fin }: Seleccion) =>
  bloque(texto, fin, fin, TABLA, { inicio: 2, fin: 2 + 'Encabezado'.length })

export function formulaEnBloque(texto: string, { inicio, fin }: Seleccion): Cambio {
  const dentro = texto.slice(inicio, fin)
  return bloque(texto, inicio, fin, `$$\n${dentro}\n$$`, { inicio: 3, fin: 3 + dentro.length })
}

/**
 * ¿Queda abierta una fórmula al final de `texto`? Cuenta los `$` y los `$$`
 * sin escapar. Es una aproximación, no el parser de remark-math: no mira los
 * bloques de código, donde un `$` no abre nada. Si un guion llega a tener
 * código con dólares, `mk` y `dm` pueden no saltar después de él.
 */
function dentroDeFormula(texto: string): boolean {
  let enLinea = false
  let enBloque = false
  for (let i = 0; i < texto.length; i++) {
    if (texto[i] === '\\') {
      i++ // `\$` es un dólar escrito, no una fórmula
    } else if (texto[i] === '$' && texto[i + 1] === '$') {
      if (!enLinea) enBloque = !enBloque
      i++
    } else if (texto[i] === '$' && !enBloque) {
      enLinea = !enLinea
    }
  }
  return enLinea || enBloque
}

/**
 * U5: `mk` y `dm`, recién escritos antes de `cursor`, se cambian por una
 * fórmula en línea o en bloque, como en Latex Suite. Solo al principio de una
 * palabra, para que «administrar» no abra nada, y fuera de las fórmulas,
 * donde `dm` es un diferencial de masa. `null` si no hay nada que cambiar.
 */
export function disparador(texto: string, cursor: number): Cambio | null {
  const escrito = texto.slice(Math.max(0, cursor - 2), cursor)
  if (escrito !== 'mk' && escrito !== 'dm') return null

  const desde = cursor - 2
  if (desde > 0 && !/\s/.test(texto[desde - 1])) return null
  if (dentroDeFormula(texto.slice(0, desde))) return null

  if (escrito === 'mk') {
    return { desde, hasta: cursor, texto: '$$', seleccion: { inicio: desde + 1, fin: desde + 1 } }
  }
  return bloque(texto, desde, cursor, '$$\n\n$$', { inicio: 3, fin: 3 })
}
