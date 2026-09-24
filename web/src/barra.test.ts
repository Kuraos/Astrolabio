/**
 * Criterios T2–T5 y W2–W3 de la Fase 4: las acciones de la barra del guion.
 *
 * En los textos de prueba, `«…»` marca la selección y `‸` el cursor. Así cada
 * caso se lee como se vería en el campo, antes y después de pulsar el botón.
 */

import { describe, expect, it } from 'vitest'

import {
  cita,
  cursiva,
  disparador,
  enlace,
  formulaEnBloque,
  formulaEnLinea,
  imagen,
  lista,
  negrita,
  tabla,
  titulo,
  type Cambio,
  type Seleccion,
} from './barra'

type Accion = (texto: string, seleccion: Seleccion) => Cambio

function partir(conMarcas: string): { texto: string; seleccion: Seleccion } {
  const cursor = conMarcas.indexOf('‸')
  if (cursor >= 0) {
    return { texto: conMarcas.replace('‸', ''), seleccion: { inicio: cursor, fin: cursor } }
  }
  const inicio = conMarcas.indexOf('«')
  const fin = conMarcas.indexOf('»') - 1
  return { texto: conMarcas.replace('«', '').replace('»', ''), seleccion: { inicio, fin } }
}

function marcar(texto: string, { inicio, fin }: Seleccion): string {
  if (inicio === fin) return texto.slice(0, inicio) + '‸' + texto.slice(inicio)
  return texto.slice(0, inicio) + '«' + texto.slice(inicio, fin) + '»' + texto.slice(fin)
}

/** Pulsa el botón sobre el texto marcado y devuelve cómo queda, marcado. */
function pulsar(accion: Accion, conMarcas: string): string {
  const { texto, seleccion } = partir(conMarcas)
  const cambio = accion(texto, seleccion)
  const nuevo = texto.slice(0, cambio.desde) + cambio.texto + texto.slice(cambio.hasta)
  return marcar(nuevo, cambio.seleccion)
}

describe('T2: negrita, cursiva y fórmula en línea envuelven', () => {
  it('la negrita envuelve la selección y la deja seleccionada', () => {
    expect(pulsar(negrita, 'hola «mundo»')).toBe('hola **«mundo»**')
  })

  it('sin selección, deja el cursor entre las marcas', () => {
    expect(pulsar(negrita, 'hola ‸')).toBe('hola **‸**')
  })

  it('la cursiva usa un asterisco', () => {
    expect(pulsar(cursiva, 'hola «mundo»')).toBe('hola *«mundo»*')
  })

  it('la fórmula en línea usa dólares', () => {
    expect(pulsar(formulaEnLinea, 'la masa «M_\\odot»')).toBe('la masa $«M_\\odot»$')
  })

  it('quita la negrita si la selección la incluye', () => {
    expect(pulsar(negrita, 'hola «**mundo**»')).toBe('hola «mundo»')
  })

  it('quita la negrita si las marcas están justo fuera', () => {
    expect(pulsar(negrita, 'hola **«mundo»**')).toBe('hola «mundo»')
  })

  it('pulsar dos veces sin escribir deja el texto como estaba', () => {
    expect(pulsar(negrita, 'hola **‸**')).toBe('hola ‸')
  })

  it('la cursiva sobre una negrita no la toma por cursiva', () => {
    // `**` empieza por `*`: contar los asteriscos es lo que las distingue.
    expect(pulsar(cursiva, 'hola **«mundo»**')).toBe('hola ***«mundo»***')
  })

  it('quitar la negrita de negrita y cursiva deja la cursiva', () => {
    expect(pulsar(negrita, 'hola ***«mundo»***')).toBe('hola *«mundo»*')
  })

  it('quitar la cursiva de negrita y cursiva deja la negrita', () => {
    expect(pulsar(cursiva, '«***mundo***»')).toBe('«**mundo**»')
  })

  it('quita la fórmula en línea', () => {
    expect(pulsar(formulaEnLinea, 'a $«x»$ b')).toBe('a «x» b')
  })

  it('el cambio no toca el texto de alrededor', () => {
    // La vista sustituye solo este tramo: si fuera el guion entero, el
    // deshacer y el desplazamiento del campo saltarían con cada botón.
    expect(negrita('a b c', { inicio: 2, fin: 3 })).toMatchObject({ desde: 2, hasta: 3 })
  })
})

describe('T3: enlace e imagen dejan la URL lista para pegar', () => {
  it('el enlace envuelve la selección y selecciona url', () => {
    expect(pulsar(enlace, 'ver «el paper»')).toBe('ver [el paper](«url»)')
  })

  it('sin selección, el texto del enlace es «enlace»', () => {
    expect(pulsar(enlace, 'ver ‸')).toBe('ver [enlace](«url»)')
  })

  it('la imagen usa la selección como descripción', () => {
    expect(pulsar(imagen, 'foto de «M31»')).toBe('foto de ![M31](«url»)')
  })

  it('sin selección, la descripción de la imagen es «descripción»', () => {
    expect(pulsar(imagen, '‸')).toBe('![descripción](«url»)')
  })
})

describe('T4: título, lista y cita actúan sobre líneas enteras', () => {
  it('el título pone ### en la línea del cursor y lo deja al final', () => {
    expect(pulsar(titulo, 'Intro\nEl Sol‸ es\nfin')).toBe('Intro\n### El Sol es‸\nfin')
  })

  it('en una línea vacía, el título deja el cursor listo para escribirlo', () => {
    expect(pulsar(titulo, 'a\n‸')).toBe('a\n### ‸')
  })

  it('un título de otro nivel pasa a nivel 3', () => {
    // En la nota del vault el guion va bajo `## Guion`: un `##` la partiría.
    expect(pulsar(titulo, '## Viejo‸')).toBe('### Viejo‸')
  })

  it('quita el título si ya es de nivel 3', () => {
    expect(pulsar(titulo, '### Hecho‸')).toBe('Hecho‸')
  })

  it('la lista pone un guion en cada línea con texto y respeta las vacías', () => {
    expect(pulsar(lista, '«uno\ndos\n\ntres»')).toBe('«- uno\n- dos\n\n- tres»')
  })

  it('la lista solo añade el guion a las líneas que no lo tienen', () => {
    expect(pulsar(lista, '«- uno\ndos»')).toBe('«- uno\n- dos»')
  })

  it('quita la lista si todas las líneas la tienen', () => {
    expect(pulsar(lista, '«- uno\n- dos»')).toBe('«uno\ndos»')
  })

  it('la cita pone > al principio', () => {
    expect(pulsar(cita, '«una frase»')).toBe('«> una frase»')
  })

  it('una selección a medias abarca las líneas enteras', () => {
    expect(pulsar(lista, 'ab«c\nd»e')).toBe('«- abc\n- de»')
  })

  it('una selección que acaba al empezar una línea no la incluye', () => {
    // Es lo que pasa al seleccionar una línea arrastrando hasta la siguiente.
    expect(pulsar(lista, '«uno\n»dos')).toBe('«- uno»\ndos')
  })

  it('funciona en la primera línea aunque esté vacía', () => {
    expect(pulsar(lista, '‸\nsegunda')).toBe('- ‸\nsegunda')
  })
})

describe('T5: tabla y fórmula en bloque van en líneas propias', () => {
  // Con el primer encabezado seleccionado, para escribir encima.
  const TABLA = '| «Encabezado» | Encabezado |\n| --- | --- |\n| Celda | Celda |'

  it('en un guion vacío no añade líneas en blanco', () => {
    expect(pulsar(tabla, '‸')).toBe(TABLA)
  })

  it('al final de un párrafo deja una línea en blanco antes', () => {
    expect(pulsar(tabla, 'Texto.‸')).toBe(`Texto.\n\n${TABLA}`)
  })

  it('entre dos párrafos completa las líneas en blanco que falten', () => {
    expect(pulsar(tabla, 'Texto.\n‸\nMás.')).toBe(`Texto.\n\n${TABLA}\n\nMás.`)
  })

  it('no duplica las líneas en blanco que ya hay', () => {
    expect(pulsar(tabla, 'Texto.\n\n‸\n\nMás.')).toBe(`Texto.\n\n${TABLA}\n\nMás.`)
  })

  it('la tabla no borra lo seleccionado', () => {
    expect(pulsar(tabla, 'Datos «clave»')).toBe(`Datos clave\n\n${TABLA}`)
  })

  it('la fórmula en bloque deja el cursor en su línea del medio', () => {
    expect(pulsar(formulaEnBloque, '‸')).toBe('$$\n‸\n$$')
  })

  it('la fórmula en bloque envuelve la selección', () => {
    expect(pulsar(formulaEnBloque, 'Texto.\n«E = mc^2»')).toBe('Texto.\n\n$$\n«E = mc^2»\n$$')
  })
})

describe('W3: mk y dm abren fórmula, como en Latex Suite', () => {
  /** Escribe hasta el cursor y devuelve cómo queda, o `null` si nada salta. */
  function escribir(conMarcas: string): string | null {
    const { texto, seleccion } = partir(conMarcas)
    const cambio = disparador(texto, seleccion.inicio)
    if (cambio === null) return null
    const nuevo = texto.slice(0, cambio.desde) + cambio.texto + texto.slice(cambio.hasta)
    return marcar(nuevo, cambio.seleccion)
  }

  it('mk al principio del guion abre una fórmula en línea', () => {
    expect(escribir('mk‸')).toBe('$‸$')
  })

  it('mk tras un espacio abre una fórmula en línea', () => {
    expect(escribir('la masa mk‸')).toBe('la masa $‸$')
  })

  it('dm abre una fórmula en bloque, en líneas propias', () => {
    expect(escribir('Texto.\ndm‸')).toBe('Texto.\n\n$$\n‸\n$$')
  })

  it('no salta dentro de una palabra', () => {
    // «adm…», de «administrar», acaba en dm.
    expect(escribir('adm‸')).toBeNull()
  })

  it('no salta dentro de una fórmula en línea', () => {
    // Ahí dm es un diferencial de masa.
    expect(escribir('$\\int \\rho\\, dm‸')).toBeNull()
  })

  it('no salta dentro de una fórmula en bloque', () => {
    expect(escribir('$$\nx + dm‸')).toBeNull()
  })

  it('salta después de cerrar una fórmula', () => {
    expect(escribir('$x$ y mk‸')).toBe('$x$ y $‸$')
  })

  it('un dólar escapado no abre fórmula', () => {
    expect(escribir('cuesta \\$5 y mk‸')).toBe('cuesta \\$5 y $‸$')
  })

  it('otras dos letras no hacen nada', () => {
    expect(escribir('hola‸')).toBeNull()
  })
})
