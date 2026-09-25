# Sistema de diseño — Astrolabio

Cómo se ve la interfaz, sacado del código que ya existe (`web/src/`) y no de
una plantilla. Una pantalla nueva debe parecer parte de la misma aplicación:
antes de inventar una clase, busca la que ya usa un panel parecido.

Todo se escribe con las clases de Tailwind 4, sin tokens propios: la paleta
es la de Tailwind (`@import "tailwindcss"` en `web/src/index.css`). Los
contrastes de este documento están calculados con los valores OKLCH de
Tailwind 4.3 convertidos a sRGB, con la transparencia compuesta sobre su
fondo, como la pinta el navegador.

## 1. Dirección

Una herramienta de taller para dos personas, no una web de marca: oscura,
sobria y densa. Un solo color tiene significado propio —el ámbar de «te
toca»—, el rosa se reserva para los errores y todo lo demás es la escala
`slate`. No hay sombras, ni iconos de biblioteca, ni animaciones. Lo único con
tipografía cuidada es el guion renderizado, porque es lo que se lee.

Solo hay tema oscuro.

## 2. Color

Contraste sobre el fondo en que se usa; WCAG AA pide 4.5:1 para texto normal.

| Papel | Clases | sRGB aprox. | Contraste |
|---|---|---|---|
| Fondo de la página | `bg-slate-950` | `#020618` | — |
| Panel | `bg-slate-900/60` sobre la página | `#0a1023` | — |
| Campo | `bg-slate-900` | `#0f172b` | — |
| Borde de panel, separadores | `border-slate-800`, `divide-slate-800` | — | 1.4 (decorativo) |
| Borde de campo y de botón secundario | `border-slate-700` | — | 1.8 |
| Borde con foco | `focus:border-slate-500` | — | 4.0 |
| Texto principal | `text-slate-100` | `#f1f5f9` | 17.2 |
| Texto con algo menos de peso | `text-slate-200`, `text-slate-300` | `#e2e8f0`, `#cad5e2` | 15.3, 12.7 |
| Etiquetas y texto secundario | `text-slate-400` | `#90a1b9` | 7.2 |
| Metadatos, títulos de panel, motivos | `text-slate-500` | `#62748e` | **4.0** |
| Vacíos, «Cargando…», flechas | `text-slate-600` | `#45556c` | **2.5** |
| Te toca | `text-amber-200`, sobre `bg-amber-400/15` en la insignia | — | 11.5 |
| Aviso que no bloquea | `text-amber-300/80` | — | 8.6 |
| Error | `border-rose-900/60 bg-rose-950/40 text-rose-200` | — | 13.0 |
| Error en una línea | `text-rose-300/80` | — | 6.6 |
| Hecho (exportación) | `border-emerald-900/60 bg-emerald-950/30 text-emerald-200` | — | 14.0 |
| Botón primario | `bg-slate-100 text-slate-900` | — | 16.3 |

Los contrastes en negrita no llegan a AA: ver §9.

## 3. Tipografía

- **Familia**: la del sistema, la `font-sans` de Tailwind (Segoe UI en
  Windows). El guion se escribe en `font-mono` (Consolas en Windows). No se
  carga ninguna fuente.
- **Tamaños**:

  | Clase | Tamaño | Uso |
  |---|---|---|
  | `text-2xl font-semibold tracking-tight` | 24 px | Nombre de la app |
  | `text-lg font-semibold` | 18 px | Título de la pieza |
  | `text-sm` | 14 px | Tarjetas del tablero, formularios de entrada y de pieza nueva |
  | `text-xs` | 12 px | Casi todo dentro de los paneles |
  | `text-[11px]` | 11 px | Insignias y la ruta del archivo exportado |

- **Título de panel**: `text-xs font-medium uppercase tracking-wider
  text-slate-500`.
- **Pesos**: `font-semibold` para títulos, `font-medium` para nombres,
  títulos de panel y el botón primario. Nada más grueso.
- **Guion renderizado**: la clase `.prosa` de `index.css`, con estas reglas:
  - títulos de 1.125, 1 y 0.9 rem en `slate-100`;
  - listas con sangría; las de tareas, sin viñeta;
  - código sobre `slate-800` y citas con borde `slate-700`;
  - tablas con bordes `slate-700` y encabezado en `slate-100`;
  - notas al pie bajo una línea `slate-800`, con el rótulo oculto a la vista;
  - KaTeX en bloque con scroll horizontal.

## 4. Espaciado

La escala de Tailwind, de 4 en 4 px (`--spacing: 0.25rem`):

- Página: `p-6`, y `space-y-6` entre bloques.
- Panel: `p-4`, y `space-y-3` entre lo que hay dentro; listas con
  `space-y-1` o `space-y-2`.
- En línea: `gap-2` o `gap-3`.
- Botones: `px-3 py-1.5`. Campos y avisos: `px-3 py-2`. Botón de formulario:
  `px-3 py-2.5`.

## 5. Radios, bordes y sombras

- `rounded-lg` (8 px): paneles y el editor del guion.
- `rounded-md` (6 px): botones, campos, avisos, filas del catálogo y tarjetas
  del tablero.
- `rounded` (4 px): insignias.
- Bordes de 1 px en lugar de sombras. No hay sombras.

## 6. Componentes

Los de referencia viven en `web/src/App.tsx`: `Panel`, `Campo`, `Aviso` y
`Turno`. No se exportan, y `Pieza.tsx` repite su marcado.

| Componente | Clases | Dónde |
|---|---|---|
| Panel | `rounded-lg border border-slate-800 bg-slate-900/60 p-4`, con su título de panel | `Panel` |
| Campo con etiqueta | `<label>` con la etiqueta en `text-xs text-slate-400`; el campo, `w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-slate-500` | `Campo` |
| Botón primario | `rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-900 disabled:opacity-40` | Guardar, transiciones hacia adelante |
| Botón primario de formulario | `w-full rounded-md bg-slate-100 px-3 py-2.5 text-sm font-medium text-slate-900` | Entrar. «Crear pieza», igual pero sin `w-full`: a 1024 px pesaría más que el tablero |
| Botón secundario | `rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40` | Devolver, Reformular, Salir, Añadir enlace, Crear la carpeta |
| Botón de texto | `text-xs text-slate-400 hover:text-slate-200` | ← Piezas, Quitar, Actualizar, Copiar ruta |
| Aviso de error | `rounded-md border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-xs text-rose-200`, con `role="alert"` | `Aviso` |
| Aviso que no bloquea | `text-xs text-amber-300/80` | «sin guardar», «Guarda el guion antes de moverla», «Checklist: quedan 2 de 3 tareas. Se puede mover igual.», «atrasada» |
| Insignia de turno | `rounded px-2 py-0.5 text-[11px]`, con `bg-amber-400/15 text-amber-200` si te toca y `text-slate-400` si no | `Turno` |
| Insignia de rol | `rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300` | Sesión |
| Fila de lista | `rounded-md px-2 py-2.5 hover:bg-slate-800/60`, dentro de `divide-y divide-slate-800`. Si filtra, la elegida lleva `bg-slate-800/60` y `aria-pressed` | Catálogo de etiquetas |
| Nota de filtro | `mb-2 flex items-baseline justify-between gap-3 text-xs text-slate-400`: «Solo las de» con la etiqueta en `text-slate-100`, y «Ver todas» como botón de texto. Va en cada panel filtrado | Tablero, semanas |
| Columna del tablero | `<section>` con el estado en `text-xs font-medium uppercase tracking-wider text-slate-400` y la cuenta a la derecha, y sus tarjetas en `space-y-2`. Las columnas, en `grid gap-4 md:grid-cols-3 lg:grid-cols-6` | Tablero |
| Tarjeta del tablero | `<button>` con `group flex w-full flex-col gap-1.5 rounded-md border border-slate-800 px-2 py-2 text-left hover:bg-slate-800/60`: el título en `text-sm text-slate-100`, con la flecha `→` a su derecha en `text-slate-600 group-hover:text-slate-300`, y debajo, en `text-xs text-slate-400`, el turno, las fechas mientras sigan pendientes («entrega 2 de oct»), cuántas tareas quedan («queda 1 de 2 tareas») y si falta el guion. Esa línea lleva `empty:hidden`, y el hueco es `gap` y no `space-y`, para que desaparezca con ella | Tablero |
| Enlace externo | `underline decoration-slate-600 underline-offset-2 hover:decoration-slate-300`, con `target="_blank" rel="noopener noreferrer"` | Material |
| Miniatura | `aspect-square w-full rounded-md bg-slate-950 object-contain`, en una rejilla `grid grid-cols-3 gap-2 md:grid-cols-6`, con el nombre, el tamaño y la fecha debajo en `text-[11px]` | Material |
| Editor del guion | `textarea` en `font-mono text-xs leading-relaxed`, con la vista previa `.prosa` al lado | Vista de la pieza |
| Botón de la barra | `rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:border-slate-500 hover:text-slate-100`; negrita y cursiva, en su propio estilo | Barra del guion |
| Selector | `<select>` con las clases del campo, en `text-xs`, dentro de un `<label>` con su nombre en `text-xs text-slate-400` | Tema de la pieza |
| Campo de fecha | `<input type="date">` con las clases del campo, en `text-xs` y con `scheme-dark`, sin el cual el icono del calendario sale negro sobre el campo. Se guarda al salir de él o tras 800 ms sin cambios, no en cada tecla | Fechas de la pieza |
| Semana | Su título en `text-xs font-medium text-slate-300` («Semana del 21 de sept»), con « · esta semana» en `text-slate-400` o « · atrasada» en `text-amber-300/80`. Debajo, una fila por entrada, `-mx-2 flex items-baseline gap-3 rounded-md px-2 py-1.5 text-xs hover:bg-slate-800/60`, con el día en `w-12` («lun 28»), el tipo en `w-20` y el título, que abre la pieza | Semanas |
| Casilla | `<input type="checkbox">` con `mt-0.5 accent-slate-300`, dentro del `<label>` de su texto, en `flex cursor-pointer items-start gap-2 text-xs` | Respaldo, tareas |
| Tarea | La casilla con el texto en `text-slate-200`; hecha, el texto en `text-slate-400 line-through` y «hecha por …» debajo en `text-[11px] text-slate-400`. Un `×` la quita, como a la ficha de etiqueta | Tareas de la pieza y sueltas |
| Ficha de etiqueta | `rounded bg-slate-800 py-0.5 pl-2 pr-1 text-xs text-slate-200`, con un `×` que la quita y dice cuál en su `aria-label` | Etiquetas de la pieza |

- **Hacia adelante y hacia atrás.** Entre los botones de transición, los que
  avanzan son primarios y los que vuelven atrás (`devolver`, `reformular`)
  son secundarios y van después. Lo decide `vuelveAtras` en `flujo.ts`.
- **La barra del guion** va encima de las dos columnas, en una fila
  `flex flex-wrap gap-1` con `role="toolbar"`. No le quita el foco al guion:
  sus botones cancelan el `mousedown`, y cada acción lo devuelve al campo.
  El `title` de cada botón repite su nombre y añade el atajo, si lo hay.
- **Confirmar** es `window.confirm`, nativo, con la consecuencia escrita en la
  pregunta (`CONFIRMACIONES` en `flujo.ts`). Solo para lo que no se deshace:
  hoy, aprobar el diseño y publicar.

## 7. Estados

- **Hover**: un botón de texto pasa a un gris más claro (`slate-400` →
  `slate-200`); las filas y las tarjetas, a `bg-slate-800/60`.
- **Foco**: los campos quitan el contorno y aclaran el borde
  (`outline-none focus:border-slate-500`); los botones conservan el anillo
  del navegador.
- **Desactivado**: `disabled:opacity-40`.
- **Cargando**: el texto dice que espera, con puntos suspensivos —«Cargando…»,
  «Añadiendo…», «Creando…»—. No hay spinners.
- **Vacío**: una frase que dice qué falta o qué hacer: «Todavía no hay
  enlaces.», «Vacía. Lo que pongas en esta carpeta…».
- **Hecho**: la acción lo dice en su propio texto durante dos segundos:
  «Copiar ruta» pasa a «Copiada».
- **Error**: el aviso rosa, debajo de lo que falló.
- **Sin configurar** (el vault, Syncthing): una frase gris con el motivo. No
  es un error y no se pinta como tal.
- **Tu turno**: ámbar.

## 8. Tamaños de pantalla

- La entrada vive en una columna centrada de `max-w-lg` (512 px), con `p-6`.
- Con sesión, la columna pasa a `max-w-5xl` (1024 px): el tablero necesita
  sus seis columnas, y la pieza abierta, el guion con la vista previa al lado.
  Lo decide `App`, según haya usuario.
- El tablero pasa de una columna a tres desde `md` y a seis desde `lg`. En
  pantalla estrecha, las columnas se apilan en el orden del flujo.
- El guion y su vista previa se ponen lado a lado desde `md` (768 px); en
  escritorio, cada uno mide unos 500 px.
- La rejilla de miniaturas pasa de tres columnas a seis desde `md`, para que
  el ancho no las agrande.
- Lo largo —URLs, nombres de archivo, rutas— lleva `break-words` o
  `break-all`, y su contenedor `min-w-0`, para no desbordar.

## 9. Accesibilidad

- `lang="es"`, botones de verdad (`<button>`), también las tarjetas del
  tablero, avisos con `role="alert"` y la flecha decorativa de la tarjeta con
  `aria-hidden`. Las confirmaciones son las del navegador y funcionan con
  teclado.
- **Contraste.** De `slate-100` a `slate-400` todo cumple AA. **`text-slate-500`
  da 4.0:1 sobre el panel y `text-slate-600`, 2.5:1: no llegan al 4.5:1 que
  pide el texto de 12 px.** Hoy los usan los títulos de panel y, fuera del
  panel Material, los metadatos, los motivos y los estados vacíos.
- **Regla para lo nuevo**: el texto que hay que leer va en `text-slate-400` o
  más claro. `slate-500` y `slate-600`, solo para lo que puede no leerse,
  como la flecha de la tarjeta.
- **Bordes de campo**: `slate-700` sobre el panel da 1.8:1, por debajo del
  3:1 que WCAG 1.4.11 pide para reconocer un control. Con foco, `slate-500`
  da 4.0:1.
- **Etiquetas**: `Campo` usa `<label>`, pero los campos dentro de los
  paneles —enlace, nota, guion— solo tienen placeholder, que desaparece al
  escribir.

## 10. Voz

- Español, de tú: «Te toca», «Guarda el guion antes de moverla».
- Las palabras del flujo son las del editor (`flujo.ts`), nunca «aprobada» a
  secas: hay tres aprobaciones distintas.
- Un error dice la causa y qué hacer: «La pieza cambió de estado mientras la
  mirabas. Recarga para ver dónde está.».
- Una confirmación dice la consecuencia, no «¿Estás seguro?».
- Sin exclamaciones ni emojis.

## 11. Lo que falta unificar

Se arregla al tocar cada sitio, no de golpe:

1. El contraste de `slate-500` y `slate-600` en texto que se lee (§9). El
   panel Material ya cumple.
2. Los bordes de campo, por debajo de 3:1 (§9).
3. Los campos sin `<label>` dentro de los paneles (§9).
4. `disabled:opacity-50` en el botón «Entrar» de `App.tsx`; el resto usa 40.
5. `Panel`, `Campo` y `Aviso` no se exportan, y `Pieza.tsx` copia sus clases.
   Cuando otro archivo los necesite, se mueven a un módulo compartido en vez
   de copiarlos otra vez.
