# Sistema de diseño — Astrolabio

Cómo se ve la interfaz, sacado del código que ya existe (`web/src/`) y no de
una plantilla. Una pantalla nueva debe parecer parte de la misma aplicación:
antes de inventar una clase, busca la que ya usa una pantalla parecida.

La identidad se llama **Control** y llegó con la Fase 7
([alcance](fase-7-identidad.md), [ADR 0014](adr/0014-identidad-con-tokens-y-fuentes-propias.md)).
Se diseñó en un canvas antes de programarla, con una hoja, «C · Sistema», de
la que sale este documento. Donde el código se apartó de ella —el mensaje del
error va en tinta, y las fichas y la barra del guion, con la línea fuerte—,
manda lo que dice aquí.

Los colores y los estilos de texto son tokens de Tailwind 4, declarados una
sola vez en `web/src/index.css`, y la paleta por defecto de Tailwind está
vacía: solo existen los de aquí. Los contrastes están calculados con la
fórmula de WCAG 2.1, con la transparencia compuesta sobre su fondo, como la
pinta el navegador.

## 1. Dirección

Una herramienta de taller para dos personas, no una web de marca: negra,
densa y con una identidad propia. Sus referentes son el manual gráfico de la
NASA de 1975 y las consolas de Mission Control: una grotesca con eje de
anchura, una mono para los rótulos y un solo color de señal.

- **El naranja es solo «te toca».** Lo que avanza la pieza es un botón en
  tinta, no en naranja.
- **El rosa avisa**: lo atrasado, lo que está sin guardar. Si además bloquea
  es un error, y va en caja con su rótulo.
- **Invertido —fondo en tinta— es seleccionado o actual**: la etiqueta que
  filtra, la pestaña elegida, el día de hoy y el estado de la pieza cuando no
  te toca.
- **Sin paneles ni sombras**: las estaciones se separan con líneas de 1 px.
  Esquinas rectas.
- Sin iconos de biblioteca ni animaciones. Lo único que se dibuja son las
  flechas, en texto, y el aspa de los huecos de imagen del boceto.

Solo hay tema oscuro.

## 2. Color

Contraste sobre el fondo en que se usa; WCAG AA pide 4,5:1 para texto y 3:1
para el borde que identifica un control.

| Papel | Token y clase | Valor | Contraste |
|---|---|---|---|
| Fondo de la página | `page`, `bg-page` | `#0a0a0b` | — |
| Superficie: el editor del guion, las miniaturas | `surface` | `#111113` | — |
| Encima: fila o tarjeta bajo el puntero, ficha de etiqueta | `raised` | `#151517` | — |
| Línea tenue: entre filas de una lista y entre días | `line-faint` | `#1e1e21` | 1,2 (decorativa) |
| Línea: estaciones, columnas, barras de la pista | `line` | `#2b2b2f` | 1,4 (decorativa) |
| Línea fuerte: inicio de semana, fichas, grupos de la barra | `line-strong` | `#4a4a50` | 2,3 (decorativa) |
| Borde de control: campos y botones secundarios | `control` | `#6b6b70` | **3,7** |
| Tinta: texto, botón primario, lo invertido | `ink` | `#f3f3f0` | 17,8 · 17,0 sobre superficie |
| Prosa: el guion y las notas | `prose` | `#dcdcd8` | 14,4 · 13,7 sobre superficie |
| Tinta 2: rótulos de campo, lo secundario | `ink-2` | `#a3a3a8` | 7,9 · 7,3 sobre encima |
| Tinta 3: metadatos | `ink-3` | `#8b8b91` | 5,8 · 5,4 sobre encima |
| Señal: solo «te toca» | `signal` | `#ff6a2b` | 6,9 · el fondo sobre ella, 6,9 |
| Alerta: atrasada, sin guardar, errores | `alert` | `#ffa3bd` | 10,6 · 9,5 en la caja de error |

Y los pares que no son texto sobre fondo:

- **La caja de error**: `bg-alert/8`, que sobre la página compone `#1e1619`.
  El mensaje, en tinta, da 16,0.
- **Lo invertido**: el fondo sobre tinta da 17,8; el dato de la etiqueta que
  filtra, `text-line` sobre tinta, 12,7.
- **Naranja y rosa difieren en luminosidad, no solo en tono**: ΔL\* = 13,6.
  Con tritanopía simulada (Machado 2009) siguen a ΔE = 42. El rosa del canvas,
  `#ff6b93`, tenía casi la luminancia del naranja y se cambió por eso.

## 3. Tipografía

- **Familias**: Archivo (anchura de 62 a 125 %, peso de 100 a 900) para todo
  el texto, y Martian Mono (anchura de 75 a 112,5 %) para los rótulos, los
  datos y el editor del guion. Las sirve la propia app
  ([ADR 0014](adr/0014-identidad-con-tokens-y-fuentes-propias.md)). Las
  fórmulas, con las fuentes de KaTeX.
- **Los tres estilos que se repiten**, con `@utility` en `index.css`:

  | Clase | Qué es | Uso |
  |---|---|---|
  | `heading-station` | Archivo 800, anchura 125 %, 0,875 rem, +0,04 em, mayúsculas | Título de estación: «Traspaso», «Semanas» |
  | `mono-label` | Martian Mono, anchura 87,5 %, 0,6875 rem, +0,06 em, mayúsculas | Rótulos, botones, turnos, números de columna |
  | `mono-data` | Martian Mono, anchura 75 %, 0,6875 rem | Datos: fechas, recuentos, quién |

- **Tamaños**:

  | Qué | Clases |
  |---|---|
  | La marca, en la entrada | `text-[clamp(2rem,10vw,8rem)] font-black font-stretch-expanded` |
  | La marca, en la barra | `text-xl font-extrabold font-stretch-expanded` |
  | El número de «te toca» | `text-[120px] font-black font-stretch-extra-condensed` |
  | Los recuentos de la franja | `text-[76px] font-extrabold font-stretch-extra-condensed` |
  | El título de la pieza | `text-[clamp(2rem,4vw,3.25rem)] font-bold font-stretch-semi-condensed` |
  | El nombre del estado en la franja | `text-[15px] font-semibold` |
  | El título de la tarjeta | `text-base font-medium` |
  | La prosa del guion | `text-[15px] leading-[1.65] text-prose` |
  | El texto de la interfaz | `text-sm` |
  | El editor del guion | `font-mono text-[12.5px] leading-[1.75] font-stretch-condensed` |

- **Mayúsculas para lo fijo, mayúscula inicial para lo demás.** Los rótulos,
  los botones y los turnos van en mayúsculas con `mono-label`. Lo demás —los
  estados del flujo (`enPalabras`), las líneas de una tarjeta, «Hecha por…»—
  empieza con mayúscula, como una frase: «Investigación», «Entrega 2 de oct»
  (cambiado el 2026-09-25, a pedido de Johan). Lo que es un identificador va
  como está: los usuarios, las etiquetas y los dominios. En el código el texto
  se escribe en caja normal: la mayúscula de `mono-label` la pone el CSS, y el
  lector de pantalla lee la palabra, no letras sueltas.

## 4. Espaciado

La escala de Tailwind, de 4 en 4 px (`--spacing: 0.25rem`):

- **Ancho**: `ANCHO` (`ui.tsx`), hasta 1440 px, con `px-4`, `sm:px-6` y
  `lg:px-10`.
- **Estaciones**: el título y el contenido con `gap-4`. Entre una estación y
  la siguiente, una línea de 1 px y `pt-5`; entre columnas de la pieza, una
  línea vertical y `pl-7` o `pr-7`.
- **Filas de lista**: `py-2.5` con `border-b border-line-faint`. Tarjetas del
  tablero: `py-3.5`.
- **Botones**: `px-3.5 py-3`, y el secundario `py-[11px]` para medir lo mismo
  con su borde. Campos: `p-2.5`.

## 5. Radios, bordes y sombras

- **Esquinas rectas**: ninguna clase `rounded-*`.
- **Líneas de 1 px** en lugar de paneles y sombras. Barras de 3 px en la pista
  de estados de la pieza y en el flujo de la entrada.
- No hay sombras.

## 6. Componentes

Las piezas que se repiten viven en `web/src/ui.tsx`: `ANCHO`, `BOTON`,
`BOTON_SECUNDARIO`, `BOTON_DE_TEXTO`, `CONTROL`, `Estacion`, `Campo`,
`Pestanas` y `Aviso`. Lo que solo usa una pantalla vive en ella.

| Componente | Cómo | Dónde |
|---|---|---|
| Estación | `Estacion`: el título en `heading-station` y, si hace falta, una acción o una nota a la derecha. Las líneas que la separan las pone quien la coloca | Todas las pantallas |
| Campo con rótulo | `Campo` con un control de clase `CONTROL`: el rótulo en `mono-label text-ink-2` encima, el borde en `control`, y en tinta con el foco | Entrada, pieza nueva, nota del traspaso, enlace, fechas, cuadro, tema, caption |
| Selector | Un `<select>` con `CONTROL`, y «Sin …» como primera opción para lo que aún no se ha decidido. Sus opciones, en tinta sobre el fondo de la página (`option` en `index.css`): la lista la pinta el navegador aparte, y sin eso salía blanco sobre blanco | Tipo de pieza, propósito, nivel, tema |
| Pestañas | `Pestanas`: un grupo con borde `line-strong`, como los de la barra del guion, con cada pestaña en `mono-label`; la elegida, invertida. Los paneles los pone quien las usa, con los `id` de `idsDePestana`, y se esconden con `hidden` en vez de desmontarse cuando guardan algo que no se puede perder | Textos de la pieza |
| Botón primario | `BOTON`: tinta sobre negro | Entrar, Crear pieza, Guardar, las transiciones que avanzan |
| Botón secundario | `BOTON_SECUNDARIO`: borde `control` | Devolver, Reformular, Exportar al vault, Añadir, Crear la carpeta |
| Botón de texto | `BOTON_DE_TEXTO`: `mono-label` en `ink-2`, en tinta al pasar | ← Piezas, Quitar, Actualizar, Copiar ruta, Ver todas |
| Aviso de error | `Aviso`: caja con borde `alert` y fondo `alert/8`, el rótulo «Error» y el mensaje en tinta, con `role="alert"` | Debajo de lo que falló |
| Aviso que no bloquea | Texto en `text-alert`, a 13 px, o `mono-label text-alert` si es un rótulo | «Sin guardar», «Guarda los textos antes de moverla…», «Checklist: …», «Falta: …», «Cuadro de materiales: falta …» |
| Hecho | Caja con borde `control`, el rótulo «Escrito en» y la ruta en `mono-data`, con `role="status"` | Exportar al vault |
| Te toca, el bloque | `TeToca`: fondo `signal`, el número en grande y «de N piezas» | Tablero, arriba a la izquierda |
| Te toca, la marca | Un cuadrado de 8 px en `bg-signal` y el texto en `mono-label text-signal` | Tarjeta |
| Turno del otro | `mono-label text-ink-3`: «Le toca a Johan», «Le toca al editor» | Tarjeta |
| Franja de estados | Por columna, su número, su nombre, cuántas piezas tiene y de quién es, dicho desde quien mira (`duenoDelEstado`, en `flujo.ts`) | Tablero |
| Tarjeta | Botón con la marca de turno, el título con la flecha y los datos en `mono-data`. La entrega y la publicación vencidas —anteriores a hoy—, en `text-alert`; las publicadas, en `ink-2` | Tablero |
| Etiqueta del catálogo | Botón con `aria-pressed`; la que filtra, invertida | Tablero, columna izquierda |
| Nota de filtro | «Solo las de …», con la etiqueta en tinta, y «Ver todas» | Tablero y semanas, mientras filtra |
| Línea de tiempo | Columnas por día, colocadas por `lineaDeTiempo` (`fechas.ts`); hoy, invertido; en rosa, cada entrada vencida y el rótulo de las semanas pasadas; cada entrada, un botón que abre su pieza. Vencida es anterior a hoy, por día y no por semana, como en la tarjeta: lo decide `vencida`, en `semanas()` | Semanas, desde `md` |
| Pista de estados | Seis celdas con barra de 3 px: las que pasaron en `control`, la actual en señal si te toca o invertida si no, las que faltan en `line`. `aria-current="step"` en la actual | Pieza |
| Historia | La fecha en `mono-data`, la transición en negrita, de dónde a dónde y quién en `mono-data`, y la nota en `prose` | Traspaso |
| Ficha de etiqueta | Borde `line-strong`, fondo `raised`, y una × que dice cuál quita en su `aria-label` | Tema y etiquetas |
| Casilla | La del navegador, `size-4 accent-ink` | Tareas, respaldo, destino |
| Cuadro de materiales | Tres selectores en fila desde `sm`; los destinos, en casillas dentro de un `fieldset` con su `legend` en `mono-label`, porque una pieza puede ir a varios; y debajo, lo que falta como aviso que no bloquea | Pieza |
| Lámina | «Lámina N» en `mono-label`, con ↑, ↓ y «Quitar» como botones de texto que dicen cuál mueven en su `aria-label`; el campo, con `CONTROL`; y el recuento en `mono-data`: caracteres y palabras sin el LaTeX, y las fórmulas aparte. Con fórmula, debajo, pintada, tras una línea `line-strong` | Copy gráfico, en dos columnas desde `lg` |
| Límites del caption | Por destino, su nombre en `text-sm font-medium`, dónde va el caption si no es el pie, y las medidas en `mono-data`. Pasarse va en `text-alert` y en palabras, «1 de más»: el color solo no se oye. Sin límite comprobado, se dice | Caption |
| Lámina del boceto | Una `figure`: «Lámina N» en `mono-label` y la idea en `text-sm` encima; la lámina, una rejilla de CSS en su proporción, sobre `surface`, con líneas `line` cada celda y borde `line-strong`; debajo, «Para la edición» en `mono-label` y la nota en `ink-2`. Tres por fila desde `xl`, dos desde `sm` | Boceto |
| Elemento del boceto | En su zona de la rejilla, con «Tipo · peso» en `mono-data`. El peso, en el borde y la letra: 1, borde de 2 px en tinta sobre `raised` y 15 px en negrita; 2, borde `ink-2` y 13 px; 3, borde `control` y 12 px; 4, borde discontinuo `line-strong` y 11 px en `ink-2`. Figura y gráfica llevan el aspa, un SVG en `line-strong`, y su descripción en cursiva. En una zona de una fila, el rótulo y el texto van en línea | Boceto |
| Miniatura | `aspect-square border border-line bg-surface object-contain`, cinco por fila desde `md` | Material |
| Barra del guion | Cuatro grupos con borde `line-strong` —énfasis, bloques, lo que viene de fuera y fórmulas—, en `role="toolbar"` | Guion |
| Editor y vista previa | «Markdown» y «Vista previa» rotulan las dos mitades. El editor, sobre `surface`; la vista previa, con la clase `.prosa` de `index.css` | Pestaña «Guion» de los textos |

- **Hacia adelante y hacia atrás.** Entre los botones de transición, los que
  avanzan son primarios y los que vuelven atrás (`devolver`, `reformular`)
  son secundarios y van después. Lo decide `vuelveAtras` en `flujo.ts`.
- **La barra del guion** no le quita el foco al guion: sus botones cancelan el
  `mousedown`, y cada acción lo devuelve al campo. El `title` de cada botón
  repite su nombre y añade el atajo, si lo hay.
- **Confirmar** es `window.confirm`, nativo, con la consecuencia escrita en la
  pregunta (`CONFIRMACIONES` en `flujo.ts`). Solo para lo que no se deshace:
  hoy, aprobar el diseño y publicar.
- **La vista previa pinta con el KaTeX de `rehype-katex`**, y el CSS lo trae el
  paquete `katex`: los dos van en la misma versión, y una prueba de
  `Guion.test.tsx` falla si se separan.

## 7. Estados

- **Hover**: las filas y las tarjetas pasan a `bg-raised`; la flecha de la
  tarjeta y los botones de texto, a tinta.
- **Foco**: un contorno de 2 px en tinta, a 2 px de separación, en todo lo que
  se alcanza con el teclado (`:focus-visible`, en `index.css`). Los campos,
  además, aclaran su borde a tinta. En el editor del guion el contorno va por
  dentro, porque el marco lo pega al borde.
- **Desactivado**: `disabled:opacity-40`.
- **Cargando**: «Cargando…» en `mono-label text-ink-3`. No hay spinners.
- **Vacío**: una frase en `text-sm text-ink-2` que dice qué falta o qué hacer:
  «Todavía no hay enlaces.», «Vacía. Lo que pongas en esta carpeta…».
- **Hecho**: la acción lo dice en su propio texto durante dos segundos
  —«Copiar ruta» pasa a «Copiada»—, o en la caja de hecho.
- **Error**: el aviso en su caja, debajo de lo que falló.
- **Sin configurar** (el vault, Syncthing): una frase en `ink-2` con el motivo.
  No es un error y no se pinta como tal.
- **Tu turno**: naranja. **Lo atrasado**: rosa. **Lo seleccionado o actual**:
  invertido.

## 8. Tamaños de pantalla

Mirado a 1280 y a 375 px, sin desborde horizontal.

- Las pantallas crecen hasta 1440 px (`ANCHO`).
- **El tablero** tiene su columna izquierda y seis columnas desde `lg`; tres
  desde `md`, con la columna izquierda arriba; y una en pantalla estrecha, en
  el orden del flujo (AB5). Allí la celda de cada estado pasa de bloque alto a
  una fila, y el bloque «te toca», a una línea.
- **Las semanas** son una línea de tiempo desde `md` y una lista por debajo.
  En la lista, la fecha y el tipo de una entrada vencida van en rosa, y el
  tipo dice «atrasada», como en la línea: el color solo no lo oye el lector
  de pantalla.
- **La pieza** pone sus estaciones en dos columnas desde `lg`, y el guion con
  su vista previa, lado a lado desde `md`. En pantalla estrecha, su barra
  pasa a dos filas y la pista de estados, a dos columnas. El cuadro de
  materiales va arriba a la derecha, junto a las fechas; los textos, a todo
  el ancho, con las láminas en dos columnas y el caption junto a sus límites
  desde `lg`; y debajo, el boceto, con sus láminas en una, dos o tres
  columnas según el ancho.
- La marca de la entrada encoge con la pantalla (`clamp`).
- Lo largo —URLs, nombres de archivo, rutas, etiquetas— lleva `break-words` o
  `break-all`, y su contenedor `min-w-0`, para no desbordar.

## 9. Accesibilidad

- `lang="es"`, botones de verdad (`<button>`), también las tarjetas, las
  etiquetas del catálogo y las entradas de la línea de tiempo; avisos con
  `role="alert"`; `aria-pressed` en la etiqueta que filtra y
  `aria-current="step"` en el estado actual de la pieza.
- **Lo que es andamio lleva `aria-hidden`**: las flechas, los números de los
  días de la línea de tiempo y el flujo de fondo de la entrada. El lector de
  pantalla lee las semanas y las entradas, no 28 números.
- **Contraste**: todo el texto que se lee da al menos 4,5:1; el más bajo,
  `ink-3` sobre `raised`, 5,4. Los bordes de control, 3,7:1.
- **Todo campo tiene nombre.** Los sueltos, con rótulo visible; las filas de
  añadir —tareas y etiquetas—, con `aria-label` y el título de su estación.
- **Las pestañas siguen el patrón de ARIA**: `role="tablist"`, `tab` y
  `tabpanel`, `aria-selected` y `aria-controls`. Solo la elegida entra en el
  orden del Tab; las flechas, Inicio y Fin eligen otra y le pasan el foco.
- **Mover una lámina lleva el foco con ella**, para seguir moviéndola; en un
  extremo, al botón del otro sentido.
- **El boceto se lee por peso.** Los elementos van en el DOM del peso 1 al 4,
  que es el orden del lector de pantalla, y la rejilla los pone en su zona. El
  aspa es `aria-hidden`: la dice el rótulo «Figura».
- **Los colores que hay que distinguir difieren también en luminosidad** (§2).
- Las confirmaciones son las del navegador y funcionan con teclado.

## 10. Voz

- Español, de tú: «Te toca», «Guarda el guion antes de moverla».
- Las palabras del flujo son las del editor (`flujo.ts`), nunca «aprobada» a
  secas: hay tres aprobaciones distintas. Y el editor no lee «editor» en la
  franja del tablero (estados §6.6).
- Un error dice la causa y qué hacer: «La pieza cambió de estado mientras la
  mirabas. Recarga para ver dónde está.».
- Una confirmación dice la consecuencia, no «¿Estás seguro?».
- Sin exclamaciones ni emojis.

## 11. Lo que falta unificar

La Fase 7 cerró las cinco deudas que listaba la versión anterior: el
contraste de `slate-500` y `slate-600`, los bordes de campo, los campos sin
rótulo, el `opacity-50` de «Entrar» y las clases copiadas entre paneles.

Queda una regla para lo que venga: **si un color o un componente cambia en el
código, cambia aquí**, con su contraste recalculado. El canvas fue el punto de
partida, no la referencia.
