/**
 * Criterio AP4 de la Fase 8: los recuentos del copy gráfico y del caption.
 */

import { describe, expect, it } from 'vitest'

import { caracteres, formulas, hashtags, palabras, sinFormulas } from './recuento'

describe('caracteres: los que ve quien escribe', () => {
  it('cuenta letras con tilde como una, compuestas o no', () => {
    // «ó» precompuesta, y «o» más la tilde combinante: la misma letra.
    expect(caracteres('órbita')).toBe(6)
    expect(caracteres('órbita')).toBe(6)
  })

  it('un emoji es uno, aunque ocupe dos unidades de UTF-16', () => {
    expect('☀️'.length).toBe(2)
    expect(caracteres('☀️')).toBe(1)
    expect(caracteres('🔭')).toBe(1)
  })

  it('una familia unida con ZWJ y una bandera también son uno', () => {
    expect(caracteres('👩‍🚀')).toBe(1)
    expect(caracteres('🇨🇴')).toBe(1)
  })

  it('los espacios y los saltos de línea cuentan, como en las redes', () => {
    expect(caracteres('a b\nc')).toBe(5)
    expect(caracteres('')).toBe(0)
  })
})

describe('palabras', () => {
  it('cuenta lo que lleva letras o cifras', () => {
    expect(palabras('La luz que ves salió hace 8 minutos')).toBe(8)
  })

  it('un signo suelto o un emoji no son palabras', () => {
    expect(palabras('Sol — 8 min ☀️')).toBe(3)
  })

  it('los espacios de más no inventan palabras', () => {
    expect(palabras('  una   lámina \n\n ')).toBe(2)
    expect(palabras('')).toBe(0)
  })
})

describe('las fórmulas de una lámina se cuentan aparte', () => {
  const lamina = 'Recorre $d \\approx 1{,}496 \\times 10^{11}\\,\\mathrm{m}$ a $c$: $$t = d/c$$'

  it('cuenta las de línea y las de bloque', () => {
    expect(formulas(lamina)).toBe(3)
    expect(formulas('Sin fórmulas')).toBe(0)
  })

  it('el texto que queda es el que se lee, sin los huecos', () => {
    expect(sinFormulas(lamina)).toBe('Recorre a :')
    expect(sinFormulas('La luz $t = d/c$ tarda')).toBe('La luz tarda')
  })

  it('un dólar sin cerrar no es una fórmula', () => {
    expect(formulas('Cuesta $5')).toBe(0)
  })

  it('sin fórmulas, el texto no se toca, espacios incluidos', () => {
    expect(sinFormulas('  dos  espacios \n')).toBe('  dos  espacios \n')
  })
})

describe('hashtags', () => {
  it('cuenta cada uno, con tildes y ñ', () => {
    expect(hashtags('¿Lo sabías?\n\n#astronomía #ciencia #año_luz')).toBe(3)
  })

  it('con cifras cuenta si lleva alguna letra', () => {
    expect(hashtags('#eclipse2026 #2026eclipse #2026')).toBe(2)
  })

  it('cuenta los que van seguidos, y los de dentro de una frase', () => {
    expect(hashtags('#a #b\n#c')).toBe(3)
    expect(hashtags('Mira (#jwst) y «#hubble»')).toBe(2)
  })

  it('no cuenta lo que no es un hashtag', () => {
    expect(hashtags('Escrito en C# y &#39; en https://ejemplo.org/#seccion')).toBe(0)
    expect(hashtags('# Un título')).toBe(0)
  })
})
