# Fase 4 — Escribir con herramientas

**Alcance vigente**, acordado el 2026-09-23 con las decisiones de §7. Resuelve
el problema 2 de la [hoja de ruta](hoja-de-ruta.md). Ninguna otra
funcionalidad entra hasta que esto esté terminado según §5. La prueba de la
Fase 3 con el editor se hace en el uso y no bloquea esta.

## 1. Objetivo

Que escribir el guion sea más rápido que en un procesador de texto, sin perder
lo que lo hace mejor: markdown con LaTeX real, que llega intacto al vault (H2).

Johan lo pidió así: «es muy rudimentario; que tuviera atajos como un botón para
activar negrillas, insertar imágenes, tablas o similares sería útil». La barra
no cambia lo que se escribe, solo evita teclearlo: cada botón produce el mismo
markdown que se escribiría a mano.

## 2. Fuera de alcance — no implementar

Un editor WYSIWYG: reescribe el markdown por debajo y pone en riesgo el LaTeX,
que es H2 · resaltado de sintaxis, o cualquier editor que sustituya al campo
de texto: si el campo se queda corto, CodeMirror es el paso siguiente, con su
ADR · un motor de snippets al estilo Latex Suite: entran solo `mk` y `dm`
(U5) · autocompletar comandos de LaTeX · guardar solo, sin pedirlo · imágenes
de la carpeta de la pieza dentro del guion (§7.1).

## 3. El terreno, verificado

Mirado en el código y en el navegador el 2026-09-23, sobre la pieza de prueba
y sin guardar nada:

- **El guion es un `textarea` controlado por React** (`Pieza.tsx`), con la
  vista previa al lado: `react-markdown` con `remark-math` y `rehype-katex`.
  No tiene ningún atajo de teclado.
- **Cada columna mide 250 px.** La vista de la pieza vive en la misma columna
  de 512 px que la lista (`max-w-lg`); medido con la ventana a 1880 px. Diez
  botones no caben en 250 px.
- **Las tablas no se ven en la vista previa.** Una tabla escrita a mano sale
  como un párrafo con las barras a la vista, porque falta `remark-gfm`.
  Obsidian sí la pinta: hoy la vista previa y el vault no coinciden.
- **Un enlace de la vista previa saca de la aplicación.** Se pinta sin
  `target` y se abre en la misma pestaña, y la app no avisa al salir: el
  guion sin guardar se pierde. Con un botón de enlace habrá más enlaces que
  pulsar.
- **Asignar el valor del campo rompe el deshacer.** Con «hola» tecleado y
  « **negrita**» añadido desde el código —lo que haría un botón que llama a
  `setGuion`—, Ctrl+Z ya no hace nada: no quita la negrita ni lo tecleado.
  Insertando con `document.execCommand('insertText')`, el navegador lo trata
  como tecleado: Ctrl+Z deja «hola», Ctrl+Y lo rehace y la vista previa sigue
  a los dos.
- **En la nota del vault, el guion va bajo `## Guion`**, y detrás viene
  `## Verificación antes de publicar` (`exportador._nota`). Un título `##`
  dentro del guion partiría la plantilla en secciones que no son suyas; uno
  `###` queda dentro.
- `test_el_guion_viaja_con_su_latex` ya vigila que el LaTeX llegue intacto al
  vault (H2).
- **No hay pruebas del cliente**: `check` es `tsc` y `vite build`
  ([`AGENTS.md`](../AGENTS.md) §5), y la CI corre ese mismo `check`.
- **Las dos dependencias previstas encajan con lo instalado.** `remark-gfm`
  4.0.1 usa el mismo `unified` 11 que `react-markdown` 10, y vitest 5.0.1
  admite el Vite 7 del proyecto. Las funciones que transforman el texto no
  necesitan DOM, así que vitest no pide jsdom.
- Johan usa Latex Suite en Obsidian. Sus atajos de fábrica para abrir una
  fórmula son `mk`, en línea, y `dm`, en bloque
  ([README del plugin](https://github.com/artisticat1/obsidian-latex-suite)).

## 4. Criterios de aceptación

### T. La barra

- **T1** Una barra sobre el guion con diez botones: negrita, cursiva, título,
  lista, cita, enlace, tabla, fórmula en línea, fórmula en bloque e imagen
  (§7.2).
- **T2** Negrita, cursiva y fórmula en línea envuelven la selección: `**…**`,
  `*…*`, `$…$`. Sin selección, insertan las marcas y dejan el cursor entre
  ellas. Si la selección ya está envuelta con esa marca, el botón la quita.
- **T3** Enlace e imagen envuelven la selección —o las palabras «enlace» y
  «descripción», si no la hay— y dejan seleccionado `url` para pegar encima:
  `[…](url)`, `![…](url)`. La imagen es siempre por URL pública, que Obsidian
  también pinta (§7.1).
- **T4** Título, lista y cita actúan sobre las líneas enteras de la
  selección, con `### `, `- ` y `> ` al principio de cada una; si todas lo
  tienen ya, se lo quitan. El título es de nivel 3 (§3).
- **T5** Tabla y fórmula en bloque van en líneas propias, con una línea en
  blanco antes y otra después, que es lo que necesita el markdown para
  reconocerlas. La tabla, de dos columnas con su encabezado. La fórmula, `$$`
  en una línea, el cursor en la siguiente y `$$` en la tercera.
- **T6** Nada de lo que inserta la barra es sintaxis que Obsidian no pinte:
  es el mismo markdown con LaTeX que se escribiría a mano.

### U. Atajos y deshacer

- **U1** Ctrl+B, Ctrl+I y Ctrl+K hacen lo mismo que negrita, cursiva y
  enlace, solo con el foco en el guion. En Mac, con Cmd.
- **U2** Ctrl+Z deshace de un paso lo que hizo un botón o un atajo, y Ctrl+Y
  lo rehace, como si se hubiera tecleado (§3). Se comprueba en el navegador:
  la pila de deshacer es suya, y ninguna prueba sin DOM la alcanza.
- **U3** Después de pulsar un botón, el foco vuelve al guion, para seguir
  escribiendo sin tocar el ratón.
- **U4** Ctrl+S guarda el guion, igual que el botón «Guardar», y el navegador
  no abre su «Guardar como» (§7.3).
- **U5** `mk` y `dm`, al escribirlos, se cambian por una fórmula en línea
  (`$…$`) y una en bloque (`$$…$$`), con el cursor dentro, como en Latex
  Suite (§7.3). Solo al principio de una palabra —«administrar» no abre
  nada— y fuera de las fórmulas: dentro de `$\int \rho\,dm$`, `dm` es un
  diferencial de masa y se queda como está. Ctrl+Z devuelve el `mk` o el `dm`
  escrito.

### V. La vista previa

- **V1** Las tablas se ven, con `remark-gfm`: dependencia nueva, dicha aquí
  ([`AGENTS.md`](../AGENTS.md) §6). Trae además el tachado y las listas de
  tareas, que Obsidian también pinta.
- **V2** Los enlaces de la vista previa se abren en otra pestaña, con
  `rel="noopener noreferrer"`, como los del material (S2).
- **V3** Todo lo que inserta la barra se ve igual en la vista previa que en
  Obsidian.

### W. Pruebas del cliente

- **W1** Vitest, dependencia de desarrollo nueva, dicha aquí.
  `npm --prefix web run check` pasa a ser `tsc`, vitest y `vite build`, así
  que la CI lo corre sin tocar su archivo, y `AGENTS.md` §5 lo dice.
- **W2** Cada acción de la barra es una función pura: recibe el texto y la
  selección, y devuelve lo que hay que insertar y dónde queda la selección.
  Cada una tiene sus pruebas: con selección y sin ella, a mitad de línea, con
  varias líneas, al principio y al final del guion, y quitando la marca
  (T2, T4).
- **W3** Lo mismo para `mk` y `dm` (U5): saltan al principio del guion, tras
  un espacio o un salto de línea; no saltan dentro de una palabra ni dentro
  de una fórmula, en línea o en bloque.

### X. Espacio para escribir

- **X1** Con una pieza abierta, la vista se ensancha a 1024 px
  (`max-w-5xl`): en una ventana de escritorio, guion y vista previa miden
  unos 500 px cada uno, lado a lado (§7.4). La lista de piezas sigue en
  512 px.

## 5. Definición de terminado

**Johan escribe un guion con una tabla, una fórmula en bloque abierta con
`dm` y un enlace, sin teclear su sintaxis a mano; deshace con Ctrl+Z un botón
que pulsó de más; lo guarda con Ctrl+S; y el guion se ve igual en la vista
previa y en Obsidian después de exportarlo.**

## 6. Orden sugerido

1. El ancho (X), para que la barra tenga dónde ir.
2. Vitest y las funciones de texto con sus pruebas (W, T2–T5), antes de
   ningún botón.
3. La barra y los atajos, insertando con `execCommand('insertText')` (T1,
   U1–U5), con el deshacer comprobado en el navegador.
4. La vista previa: `remark-gfm` y los enlaces en otra pestaña (V1, V2).
5. Exportar y comparar con Obsidian (T6, V3).

## 7. Decisiones — acordadas el 2026-09-23

1. **Las imágenes entran al guion solo por URL pública**, que Obsidian también
   pinta. Las de la carpeta de la pieza siguen en «Material»: su ruta no
   existe en el vault, y copiarlas allí sería escribir binarios en un
   repositorio git.
2. **La barra lleva los diez botones** de T1.
3. **Además de Ctrl+B, Ctrl+I y Ctrl+K, Ctrl+S guarda y `mk` y `dm` abren
   fórmula**, como en el Latex Suite de Johan. Son dos disparadores fijos, no
   un motor de snippets, que sigue fuera (§2).
4. **La vista de la pieza se ensancha a 1024 px**, con guion y vista previa
   lado a lado (J1). La lista de piezas se queda en 512.
