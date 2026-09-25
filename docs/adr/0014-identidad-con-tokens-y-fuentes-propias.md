# ADR 0014 — La identidad trae sus colores y sus fuentes, servidas por la app

- **Fecha**: 2026-09-25
- **Estado**: aceptada
- **Contexto**: criterios AG de `docs/fase-7-identidad.md`. Cambia dos
  decisiones de `DESIGN_SYSTEM.md` que no tenían ADR: «sin tokens propios» y
  «no se carga ninguna fuente».

## Problema

Hasta la Fase 6 la interfaz usaba la paleta de Tailwind tal cual y la fuente
del sistema. Era lo aburrido, y bastaba: no había identidad que sostener.

La identidad «Control» se apoya en dos cosas que el sistema no tiene. Una
grotesca con eje de anchura, Archivo, que va de 62 % en los numerales a 125 %
en la marca, y una mono, Martian Mono, para los rótulos. Y trece colores
propios, con el naranja reservado a «te toca».

Había que decidir de dónde salen las fuentes sin romper tres cosas que ya
estaban decididas: no hay servicios de terceros (ARCHITECTURE §2), el
navegador solo conoce un origen
([ADR 0005](0005-mismo-origen-tras-proxy.md)) y las versiones se fijan
([ADR 0013](0013-transitivas-e-imagenes-fijadas.md)).

## Decisión

### Las fuentes, como dependencias del cliente

`@fontsource-variable/archivo` y `@fontsource-variable/martian-mono`, con la
versión exacta en `web/package.json` y fijadas por el lockfile. `main.tsx`
importa sus hojas con eje de anchura (`wdth.css`), y Vite copia los `woff2` a
`/assets/`, que nginx ya cachea para siempre. El navegador del editor, por
Tailscale, no pide nada fuera de Astrolabio.

Los dos paquetes son solo CSS y archivos de fuente, OFL-1.1, sin
dependencias. Cada hoja declara sus subconjuntos con `unicode-range`, así que
el navegador baja solo el latino: 90 KB de Archivo, 102 KB más si aparece una
cursiva, y 38 KB de Martian Mono.

### Los colores y los estilos, una sola vez en `index.css`

Los trece colores, las dos familias y los tres estilos de texto que se
repiten se declaran en `@theme` y con `@utility`. La paleta por defecto de
Tailwind se vacía (`--color-*: initial`), de modo que solo existen los colores
de la identidad: una clase `slate-*` olvidada no pinta nada, y una prueba lo
vigila. `DESIGN_SYSTEM.md` dice qué es cada uno y cuánto contrasta.

## Alternativas descartadas

- **Google Fonts**, con un `<link>`. Cada carga le diría a Google quién abre
  Astrolabio, y el editor, que entra por la tailnet, dependería de un tercero
  para ver la app bien pintada.
- **Copiar los `woff2` a `web/public/`.** Sin dependencias, pero con binarios
  en el repositorio que nadie actualiza, y sin nada que diga de qué versión
  salieron. El lockfile ya cumple esa función para todo lo demás.
- **Seguir con la fuente del sistema.** Segoe UI no tiene eje de anchura, y
  sin él la identidad pierde justo lo que la distingue: la marca ancha y los
  numerales estrechos.
- **Tokens con la paleta de Tailwind debajo.** Más cómodo al migrar, pero deja
  que convivan dos sistemas sin que nada lo avise.

## Consecuencias

- Dos dependencias más en el cliente, sin transitivas. Se actualizan como el
  resto, al abrir cada fase.
- El primer arranque baja unos 130 KB de fuentes, y los siguientes, nada.
- Mientras la fuente llega se pinta la del sistema (`font-display: swap`): un
  salto breve en la primera visita.
- Cambiar un color es cambiar una línea de `index.css`, y hay que recalcular su
  contraste en `DESIGN_SYSTEM.md`.
