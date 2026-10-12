# Fase 12 — Fuentes por pieza y archivar

**Código terminado el 2026-10-11**, con las decisiones de §6; queda su prueba
de terminado (§5) con el vault y las piezas de Johan. Nace de dos tropiezos
que Johan encontró al volver al proyecto:

1. Agregar una fuente científica no era fácil ni se entendía, y todas las
   piezas enseñaban la misma lista.
2. Una pieza, una vez creada, no se podía quitar.

La Fase 11 sigue esperando al editor; esta no depende de ella.

## 1. Objetivo

- **Crear una fuente sin salir de la pieza.** Hasta ahora había que abrir
  Obsidian, crear la nota `literature` en su carpeta con su frontmatter, volver
  y pulsar «Actualizar». Ahora hay un formulario.
- **Ver qué fuentes son de esta pieza.** Elegirlas por pieza ya existía
  —`pieza.respaldo`, desde la Fase 1—, pero el panel pintaba la lista entera
  del vault igual en todas, y no se notaba.
- **Sacar del taller una pieza que sobra**, sin perder su historia.

## 2. Fuera de alcance — no implementar

Editar, renombrar o borrar una nota del vault desde la app · leer el texto de
una nota · buscar un paper por DOI y rellenar el formulario · fuentes sin nota
en el vault · borrar una pieza de verdad · borrar o marcar la copia exportada
de una pieza archivada · archivar en lote · que el editor archive.

## 3. El terreno, verificado

- **El respaldo por pieza ya estaba**: `pieza.respaldo` es una lista de
  nombres de nota, y el exportador escribe con ella `## Respaldo científico`.
  Solo cambia cómo se enseña.
- **`Investigacion/` se montaba en solo lectura**, y una prueba recorre
  `respaldo.py` para que no escriba. Las dos cosas siguen; la escritura nueva
  va en otro módulo y en un montaje más estrecho.
- **El `CLAUDE.md` de la carpeta del vault** dice qué lleva una `literature`:
  `fuente_titulo`, `fuente_tipo` (`paper` o `articulo`), `autor`, `status`,
  `fecha`, `tags`, el resumen con la fuente citada por URL, `## Nivel de
  confianza científica` y `## Relacionado` con `[[MOC-VozDelCosmos]]`.
- **Una pieza con historia no se puede borrar**: un trigger impide borrar sus
  traspasos ([ADR 0008](adr/0008-traspaso-append-only-en-la-base.md)).
- **El aviso de «te toca» y el tablero** cuentan lo que devuelve
  `GET /api/piezas`; el atasco tiene su propia consulta.

## 4. Criterios de aceptación

### BB. Una fuente nueva

- **BB1** `POST /api/fuentes`, solo para el `investigador`: el editor recibe
  403 y no se escribe nada.
- **BB2** La nota nace en `Investigacion/Recursos/` con el frontmatter de
  `literature` y sus tres secciones. Con resumen, `status: leido`; sin él,
  `por-leer`. Un DOI suelto se guarda como su enlace. El nombre del archivo es
  el que se pida o, vacío, el título, con la limpieza del
  [ADR 0007](adr/0007-como-escribe-astrolabio-en-el-vault.md).
- **BB3** Nunca pisa: si ya hay una nota con ese nombre, 409, y el archivo
  queda como estaba. El módulo no edita, mueve ni borra, y una prueba lo
  vigila en su árbol sintáctico.
- **BB4** Creada desde una pieza, queda enlazada a ella.

### BC. Las fuentes de la pieza

- **BC1** El panel separa «En esta pieza», con las enlazadas en el orden en
  que se enlazaron, de «Disponibles en el vault». Una enlazada que ya no está
  en el vault se dice y se puede quitar.
- **BC2** Las disponibles se buscan por título, nombre de nota o autor, sin
  tildes ni mayúsculas. Buscar no esconde las de la pieza.

### BD. Archivar

- **BD1** `POST /api/piezas/{id}/archivar` y `…/desarchivar`, solo para el
  `investigador`: 403 para el editor. No borra nada (§2.6). Archivar dos veces
  no mueve la fecha.
- **BD2** Una pieza archivada sale de `GET /api/piezas` —y con ello del
  tablero, de las semanas y del aviso— y de `GET /api/atasco`. Se sigue
  abriendo por su dirección.
- **BD3** `GET /api/piezas?archivadas=true` las lista. Johan las ve en la
  estación «Archivadas», las abre y las recupera, y vuelven como estaban.

### BE. Los documentos

- **BE1** El [ADR 0019](adr/0019-astrolabio-crea-fuentes.md), que enmienda el
  0001, y `AGENTS.md` §2.1, `ARCHITECTURE.md`, `DESIGN_SYSTEM.md`, `PRD.md` y
  `README.md` al día.

## 5. Definición de terminado

Johan, con su vault: crea una fuente desde una pieza, la abre en Obsidian y la
nota está bien formada, indistinguible de una hecha a mano; la ve enlazada en
esa pieza y sin enlazar en otra; y archiva las piezas de prueba, que dejan de
salir en el tablero y en el atasco.

## 6. Decisiones — acordadas con Johan el 2026-10-11

1. **Un formulario dentro de Astrolabio**, y no un botón que abra Obsidian ni
   una referencia suelta sin nota. Deroga a medias el §2.1: ver el ADR 0019.
2. **Archivar siempre, nunca borrar**, tenga la pieza historia o no. Un solo
   comportamiento, y el §2.6 queda intacto.
3. **Solo Johan archiva y recupera**, como solo él crea piezas.
4. **La copia exportada no se toca.** Si una pieza archivada tenía nota en
   `Contenido/`, la borra Johan en Obsidian.
5. **`por-leer` sin resumen.** Las notas del vault llevan `status: leido`, y
   una que nace vacía no lo está. Si el vault usa otra palabra, se cambia en
   `fuentes.py`.

## 7. Lo que apareció por el camino

- **El montaje se estrecha en vez de abrirse.** `Investigacion/` sigue en solo
  lectura y solo `Investigacion/Recursos/` se monta en escritura, encima. Si
  esa carpeta no existe, Docker la crea vacía al arrancar.
- **«Crear y no pisar» ya no lo impone el montaje**, que ahora deja escribir:
  lo impone abrir el archivo en modo `x`, que falla si existe, y la prueba de
  BB3.
- **Las enlazadas que ya no están.** Al separar las listas se vio que un
  enlace a una nota renombrada en Obsidian era invisible: seguía en la pieza y
  salía roto al exportar. Ahora se enseña.
- **Confirmar al archivar**, aunque se deshace: el botón es de texto y está
  junto a «Exportar», y la pieza desaparece de la vista de los dos. Si hay
  textos sin guardar, la pregunta lo dice.
- **El error de archivar se ve arriba**, junto al botón, y no con el de
  guardar, que está con los textos, una pantalla más abajo.
- **Las letras.** La Fase 10 ya había usado BA para sus documentos; esta
  empieza en BB.
- **Mirado el 2026-10-11** en una pila aparte, con un vault de mentira de tres
  notas, como Johan y a 490 px: se enlazó una fuente, se buscó «contaminacion»
  y quedó la del atlas, se creó una con un DOI y un `:` y un `/` en el título
  —la nota quedó como `The Hipparcos and Tycho Catalogues 1-2.md`, con su
  enlace `https://doi.org/…` y enlazada a la pieza—, y se archivó una pieza:
  salió del tablero y del atasco, el título pasó de `(2)` a `(1)`, apareció en
  «Archivadas», y al recuperarla volvió. Sin mirar: el panel a 1280 px, que en
  el navegador de la sesión no se leía, y la vista del editor.
