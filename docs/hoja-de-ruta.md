# Hoja de ruta — Fases 3 a 6

**Propuesta.** Cuatro problemas reales que Johan ve en el uso, ordenados en
fases como las anteriores. Cada fase tendrá su propio documento de alcance, con
criterios verificables y sus decisiones resueltas, que se acuerda antes de
escribir código. Este documento solo fija el orden, el contorno de cada fase y
lo que hay que decidir antes de empezarla.

La Fase 2 se cerró el 2026-09-21: sus criterios están hechos y verificados,
incluida la exportación al vault real. Queda su prueba de terminado —el editor
desde su máquina, por Tailscale—, que se hace en el uso y no bloquea lo que
sigue.

## 1. Los problemas, en palabras de Johan

1. **El material.** «A veces debo pasarle imágenes a Dathzon, links de
   referencias (como posts en Pinterest, videos del tema, etc.)». Hoy van por
   chat.
2. **El editor.** «Es muy rudimentario; que tuviera atajos como un botón para
   activar negrillas, insertar imágenes, tablas o similares sería útil».
3. **Los temas.** «Una forma de catalogar o documentar los temas de los posts
   trabajados usando etiquetas, para saber de qué hemos hablado y estamos
   hablando».
4. **Las tareas.** «Una lista de tareas compartida tipo Trello/checklist para
   poder preparar posts, líneas de tiempo y saber en qué se trabaja».

## 2. El orden

| Fase | Problema | En una línea |
|---|---|---|
| 3 — El material viaja con la pieza | 1 | Enlaces e imágenes de referencia dentro de la pieza |
| 4 — Escribir con herramientas | 2 | Barra y atajos sobre el guion, sin dejar de ser markdown con LaTeX |
| 5 — Temas y etiquetas | 3 | Etiquetas libres y un catálogo de qué se ha hablado |
| 6 — Tablero, tareas y fechas | 4 | Tablero por estado, checklist por pieza y línea de tiempo |

Es el orden de Johan, y hay razones para mantenerlo:

- **La 3 es un traspaso que hoy va por chat**, justo lo que el §1 existe para
  eliminar. Es la de más valor para el producto.
- **La 4 depende de la 3** para insertar en el guion las imágenes que ya viven
  en la pieza.
- **La 5 es pequeña**, y cuanto antes se etiquete, menos piezas habrá que
  etiquetar hacia atrás.
- **La 6 es la más grande y la de alcance más abierto.** Al final, con las
  demás andando, se sabe mejor qué hace falta de verdad.

## 3. Fase 3 — El material viaja con la pieza

**Objetivo.** Que lo que Johan le pasa al editor para hacer la pieza —enlaces e
imágenes de referencia— viva en la pieza y no en el chat.

**Entra**

- Enlaces de referencia: URL y una nota corta («la paleta de este pin», «este
  vídeo explica bien la escala»). Solo `http` y `https`, validado en el
  servidor: un `javascript:` en un enlace es un XSS esperando el clic. Se abren
  en otra pestaña, con `rel="noopener noreferrer"`.
- Imágenes en la carpeta de la pieza en Syncthing, en calidad original; la app
  guarda dónde están y muestra una miniatura (ADR 0003, sin tocar el §2.2).
- Un panel «Material» en la pieza, para los dos roles. El respaldo científico
  sigue siendo solo de Johan (ADR 0001); el material es justo lo que se
  comparte.
- Cada regla de quién añade o quita, con su prueba de 403 (§2.3).

**No entra.** Vistas previas de enlaces: traer la página desde el servidor abre
la puerta a SSRF y pide otra dependencia. Archivos de producción —vídeo,
proyectos de edición—, que siguen por Syncthing (ADR 0003). Exportar el
material al vault.

**Decidido el 2026-09-21.** Las imágenes viven en Syncthing, en calidad
original, porque el editor las necesita en sus programas de diseño y no solo en
el guion. El material lo añaden los dos, y no va al vault. El alcance completo
está en [fase-3-material.md](fase-3-material.md).

**Terminada cuando** Johan añade a una pieza un pin de Pinterest, un vídeo y
una imagen suya, y el editor, desde su sesión, los ve y los abre sin que nadie
haya mandado un mensaje.

## 4. Fase 4 — Escribir con herramientas

**Objetivo.** Que escribir el guion sea más rápido que en un procesador de
texto, sin perder lo que lo hace mejor: markdown con LaTeX real, que llega
intacto al vault (H2).

**Entra**

- Una barra sobre el guion: negrita, cursiva, título, lista, cita, enlace,
  tabla, fórmula en línea y en bloque, e imagen —de las de la pieza (fase 3) o
  por URL—.
- Atajos: Ctrl+B, Ctrl+I, Ctrl+K.
- Los botones envuelven la selección o insertan en el cursor, y **Ctrl+Z los
  deshace**. No es un detalle: hay formas de insertar texto que reescriben el
  campo entero y rompen el deshacer del navegador.
- Tablas en la vista previa, con `remark-gfm`, el complemento estándar de
  react-markdown para eso. Hoy la vista previa no las pinta; Obsidian sí.
- Vitest. Las funciones que transforman el texto son la primera lógica del
  cliente que merece prueba, que es cuando el §5 del `CLAUDE.md` dice que
  llega.

**No entra.** Un editor WYSIWYG: reescribe el markdown por debajo y pone en
riesgo el LaTeX, que es H2. Resaltado de sintaxis: si el campo de texto se
queda corto, CodeMirror es el paso siguiente, con su ADR. Snippets al estilo
Latex Suite.

**Decisiones antes de empezar**

1. **Imágenes dentro del guion.** Si el guion enlaza una imagen de la carpeta
   de la pieza en Syncthing, esa ruta no existe en Obsidian. O el guion solo
   enlaza URLs públicas y las imágenes de la pieza se quedan en «Material», o
   el exportador copia las imágenes al vault, que es escribir binarios en un
   repositorio git y pide ADR. Propuesta: lo primero.
2. **Qué botones.** La lista de arriba es una propuesta: se recorta a los que
   se usen de verdad. Si hay atajos de Latex Suite que Johan tenga en los
   dedos, este es el momento de nombrarlos.

**Decidido el 2026-09-23.** Las imágenes entran al guion solo por URL
pública; la barra lleva los diez botones; además de Ctrl+B, Ctrl+I y Ctrl+K,
Ctrl+S guarda y `mk` y `dm` abren fórmula, como en Latex Suite; y la vista de
la pieza se ensancha a 1024 px. El alcance completo está en
[fase-4-escritura.md](fase-4-escritura.md).

**Terminada cuando** Johan escribe un guion con una tabla, una fórmula en
bloque y un enlace sin teclear la sintaxis a mano, y se ve igual en la vista
previa y en Obsidian después de exportar.

## 5. Fase 5 — Temas y etiquetas

**Objetivo.** Saber de qué ha hablado Voz del Cosmos y de qué está hablando,
sin buscar en el chat ni en la memoria.

**Lo primero: tema y etiquetas no son lo mismo.** `tema` es el eje de las
métricas: el ADR 0004 pide fijar 3–4 temas para que las celdas
tema × formato × plataforma junten `n` suficiente. Las etiquetas son libres,
varias por pieza, y sirven a la memoria. Si se funden, el panel de métricas
medirá ruido.

**Entra**

- `etiquetas` en la pieza, normalizadas al escribirlas —minúscula y guiones— y
  con autocompletado de las que ya existen, para que «agujeros negros» y
  «agujero-negro» no acaben siendo dos temas.
- Un catálogo: cada etiqueta con cuántas piezas publicadas —de qué hemos
  hablado— y cuántas en curso —de qué estamos hablando—. Al pulsarla, sus
  piezas.
- Filtrar la lista de piezas por etiqueta.
- Solo conteos. Ordenar etiquetas por rendimiento es el ranking que el ADR 0004
  prohíbe con `n` pequeño.

**No entra.** Jerarquías de etiquetas, sugerencias automáticas, cruzarlas con
las notas `literature`.

**Decisiones antes de empezar**

1. **¿`tema` pasa a lista cerrada, y con qué 3–4 valores?** El ADR 0004 ya lo
   pedía y nunca se hizo.
2. **¿Las etiquetas van a `tags` en el vault?** Ahí `tags` es el único eje que
   cruza carpetas y types; mezclarlas con las de los cursos puede ser una
   conexión útil o ruido. Alternativa: anidarlas, `vdc/agujeros-negros`. Cambia
   lo que escribe el exportador, así que pide ADR.
3. **¿Tildes?** Obsidian las admite; el vault usa hoy `voz-del-cosmos`.

**Decidido el 2026-09-24.** Los temas son cuatro: Sistema Solar, Estrellas,
Galaxias y cosmología, y Exploración espacial. Las etiquetas van al vault
anidadas bajo `voz-del-cosmos` ([ADR 0011](adr/0011-las-etiquetas-viajan-al-vault.md)),
sin tildes y con ñ. `formato` y `plataforma` siguen sin editarse en la pieza.
El alcance completo está en [fase-5-temas.md](fase-5-temas.md).

**Terminada cuando** al abrir el catálogo se ve de qué se ha hablado, con
cuántas piezas publicadas y en curso por etiqueta, y las mismas etiquetas
aparecen en Obsidian.

## 6. Fase 6 — Tablero, tareas y fechas

**Objetivo.** Preparar piezas y ver en qué se trabaja sin tener un Trello
aparte.

**La advertencia.** Un Trello es alcance infinito —etiquetas de colores,
asignaciones, comentarios, adjuntos, arrastrar tarjetas, notificaciones—, y en
un proyecto de dos personas es la fase que se abandona a la mitad. Entra lo que
responde a una pregunta concreta, y nada más.

**Entra**

- **Tablero**: una columna por estado, con las piezas y su turno. Sale casi
  gratis de lo que la API ya devuelve (K4): es el «cuadro de solicitud» del
  editor en forma de tablero.
- **Checklist por pieza**: tareas con texto, hecha o no, y quién la marcó. Es
  la «checklist de traspaso» que la Fase 2 dejó fuera, en su versión que
  informa y no bloquea.
- **Fechas**: la de entrega —los «deadlines» del editor (P1)— y la de
  publicación prevista. El exportador ya tiene `fecha_publicacion` y hoy la
  escribe vacía.
- **Línea de tiempo**: las piezas por semana según sus fechas, porque el editor
  trabaja «por bloques semanales, quincenales o mensuales» (P1).

**No entra.** Arrastrar tarjetas: mover una pieza es una transición, con sus
reglas y sus confirmaciones, y en el tablero se usan los mismos botones.
Notificaciones, tareas recurrentes, comentarios en las tareas.

**Decisiones antes de empezar**

1. **¿Tareas sueltas, sin pieza** («comprar el micrófono»)? Propuesta: sí, en
   una lista aparte; cuesta que la pieza de la tarea sea opcional.
2. **¿Una tarea pendiente impide mover la pieza?** Propuesta: no. Que la
   checklist bloquee se decide cuando el hábito exista, como dice la guía de la
   conversación sobre los estados.
3. **¿La fecha de publicación del vault es la prevista o la real?** La real ya
   está en la historia: es la del traspaso `publicar`.

**Decidido el 2026-09-24.** Hay tareas sueltas, en una lista aparte, y una
tarea pendiente no impide mover la pieza. `fecha_publicacion` es la prevista
hasta publicar y la real después
([ADR 0012](adr/0012-la-fecha-de-publicacion-viaja-al-vault.md)). El tablero
reemplaza la lista, y sus tarjetas abren la pieza. El alcance completo está en
[fase-6-tablero.md](fase-6-tablero.md).

**Terminada cuando** el editor abre el tablero y sabe qué le toca y para
cuándo, y Johan ve qué le falta a cada pieza sin preguntar.

## 7. Lo que vale para todas

- **Cada fase, su documento.** Antes de escribir código, un
  `docs/fase-N-….md` con criterios verificables —las letras siguen desde la P—
  y sus decisiones resueltas, como la Fase 2.
- **Las reglas de siempre siguen.** Cada regla nueva de quién puede qué, con su
  prueba de 403 (§2.3); nada de rankings bajo el umbral (§2.7); en el vault,
  nada fuera de `03-Negocios/Voz-del-Cosmos/` (§2.5); el esquema, con
  migraciones (§4).
- **Dependencias nuevas, dichas en voz alta (§6):** Pillow, para las
  miniaturas de la fase 3; `remark-gfm` y vitest en la fase 4. Ninguna más
  prevista.
- **ADRs previstos:** la carpeta de la pieza en Syncthing (fase 3) y las
  etiquetas en el vault (fase 5).
