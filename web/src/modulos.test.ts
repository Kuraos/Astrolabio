/**
 * En Windows el disco no distingue mayúsculas, y TypeScript y Vite prueban
 * `.ts` antes que `.tsx`: con `Cuadro.tsx` junto a `cuadro.ts`, `./Cuadro`
 * resolvía a `cuadro.ts` y `tsc` fallaba en la máquina de Johan. La CI corre
 * en Linux, donde son dos archivos distintos, y no podía verlo. Esta prueba
 * falla en los dos.
 */

import { expect, it } from 'vitest'

const modulos = Object.keys(import.meta.glob('./**/*.{ts,tsx}'))

const nombre = (archivo: string) => archivo.replace(/\.tsx?$/, '').toLowerCase()

it('dos módulos del cliente nunca se llaman igual, sin contar mayúsculas ni extensión', () => {
  const repetidos = modulos.filter((a) => modulos.filter((b) => nombre(b) === nombre(a)).length > 1)
  expect(repetidos).toEqual([])
})

it('mira de verdad los módulos del cliente', () => {
  expect(modulos).toContain('./App.tsx')
})
