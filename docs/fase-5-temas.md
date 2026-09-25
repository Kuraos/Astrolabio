# Fase 5 — Temas y etiquetas

**Código terminado el 2026-09-24**, con las decisiones de §7; queda su prueba
de terminado (§5), que se hace en el uso. Resuelve el problema 3 de la
[hoja de ruta](hoja-de-ruta.md). El alcance vigente está en
[`AGENTS.md`](../AGENTS.md) §7.

## 1. Objetivo

Saber de qué ha hablado Voz del Cosmos y de qué está hablando, sin buscar en
el chat ni en la memoria.

Johan lo pidió así: «una forma de catalogar o documentar los temas de los
posts trabajados usando etiquetas, para saber de qué hemos hablado y estamos
hablando».

**Tema y etiquetas no son lo mismo.** `tema` es el eje de las métricas: el
[ADR 0004](adr/0004-sin-rankings-bajo-umbral.md) pide fijar 3–4 temas para que
las celdas tema × formato × plataforma junten `n` suficiente. Las etiquetas son
libres, varias por pieza, y sirven a la memoria. Si se funden, el panel de
métricas medirá ruido.

## 2. Fuera de alcance — no implementar

Jerarquías de etiquetas · sugerencias automáticas · cruzarlas con las notas
`literature` · renombrar o fusionar etiquetas desde la app · el panel de
métricas y cualquier orden por rendimiento (§2.7 de
[`AGENTS.md`](../AGENTS.md)) · editar `formato` y `plataforma` en la interfaz
(§7.4).

## 3. El terreno, verificado

Mirado en el código, en la carpeta del vault que lee la app y en la
documentación de Obsidian, el 2026-09-24:

- **`tema` es texto libre**: `String(100)` en la base y `str | None` en la
  API. `formato`, en cambio, ya es una lista cerrada en la API (`reel`,
  `carrusel`, `video`, `post`).
- **Ninguna pantalla edita `tema`, `formato` ni `plataforma`.** La Fase 1 los
  añadió a la pieza (H1), pero su interfaz (J) no incluía editarlos: hoy solo
  se muestran en la cabecera de la pieza, o «sin formato ni tema todavía».
- **No hay temas de los que partir.** El 2026-09-23 la base tenía dos piezas,
  las dos de prueba, y en `Contenido/` del vault solo está la nota de prueba
  «KaTeX en pantalla», con `tema: null`.
- **`respaldo` ya es una lista en la pieza** (`ARRAY` de Postgres): las
  etiquetas pueden seguir el mismo camino.
- **La lista de piezas ya se carga entera**, con su estado (`App.tsx`). El
  catálogo, el filtro y las sugerencias pueden salir de ella, sin endpoint
  nuevo.
- **El exportador escribe `tags: [voz-del-cosmos]` fijo**, y `tema` tal cual.
- **En el vault, `tags` es obligatorio en todo `type`** y es «el único eje
  transversal que cruza carpetas y types» (`CLAUDE.md` raíz del vault). Los
  que usa van en minúsculas y con guiones: `voz-del-cosmos`, `temario`.
- **Lo que Obsidian admite en un tag**
  ([documentación](https://obsidian.md/help/tags)): letras —acentuadas
  incluidas—, números, `_`, `-` y `/`, sin espacios. No puede ser solo
  números: `#1984` no es un tag. No distingue mayúsculas. La `/` anida, y
  buscar `tag:padre` encuentra también los hijos.

## 4. Criterios de aceptación

### Y. Tema y etiquetas en la pieza

- **Y1** `tema` pasa a lista cerrada con los cuatro de §7.1: Sistema Solar,
  Estrellas, Galaxias y cosmología, y Exploración espacial. La API rechaza
  con 422 cualquier otro, con su prueba, como ya hace con `formato`.
- **Y2** `etiquetas` entra en su propia migración, como lista en la pieza,
  igual que `respaldo`. Vacía por defecto.
- **Y3** El servidor normaliza cada etiqueta al guardarla, con una prueba por
  regla ([ADR 0011](adr/0011-las-etiquetas-viajan-al-vault.md)):
  - la pasa a minúsculas;
  - cambia los espacios y la `/` por guiones, porque la jerarquía la pone el
    exportador;
  - quita las tildes, pero no la ñ (§7.3);
  - quita todo lo que no sea letra, número, `_` o `-`;
  - descarta las repetidas en la misma pieza.

  Una etiqueta que queda vacía, o que es solo números, es 422: Obsidian no la
  reconocería.
- **Y4** Los dos roles cambian tema y etiquetas, como el resto de la pieza.
  Sin sesión, 401 (C5).
- **Y5** En la vista de la pieza, un selector con los cuatro temas, y las
  etiquetas como fichas que se añaden y se quitan. Al escribir una, se
  sugieren las que ya existen, con un `datalist` nativo. Se guardan al
  elegirlas, sin pasar por «Guardar», como los enlaces del material.

### Z. El catálogo

- **Z1** El catálogo sale de la lista de piezas: cada etiqueta, con cuántas
  piezas publicadas tiene —de qué hemos hablado— y cuántas en curso —de qué
  estamos hablando—. Es una función pura, con sus pruebas en vitest.
- **Z2** Vive en la pantalla de la lista. Al pulsar una etiqueta, la lista
  muestra solo sus piezas; otro clic las devuelve todas.
- **Z3** Solo conteos, en orden alfabético, para que no se lea como un
  ranking (§2.7).

### AA. El vault

Después de la Z, las letras siguen en AA.

- **AA1** El exportador escribe cada etiqueta como tag anidado bajo
  `voz-del-cosmos` —`voz-del-cosmos/agujeros-negros`—, junto a
  `voz-del-cosmos` (§7.2, [ADR 0011](adr/0011-las-etiquetas-viajan-al-vault.md)),
  y `tema` con su valor de la lista.
- **AA2** La nota sigue pasando la auditoría del vault (I3): `tags` es una
  lista y conserva `voz-del-cosmos`.

## 5. Definición de terminado

**Al abrir la lista se ve de qué se ha hablado: cada etiqueta con sus piezas
publicadas y en curso. Al pulsar una, se ven sus piezas. Cada pieza tiene uno
de los cuatro temas, y las mismas etiquetas aparecen en Obsidian, agrupadas
bajo `voz-del-cosmos`, después de exportar.**

## 6. Orden sugerido

1. El tema cerrado y las etiquetas en la base, con la normalización y sus
   pruebas (Y1–Y4).
2. El tema y las etiquetas en la vista de la pieza (Y5).
3. El catálogo como función pura con vitest, y en la pantalla de la lista
   (Z).
4. El exportador (AA).

## 7. Decisiones — acordadas el 2026-09-24

1. **Los cuatro temas son Sistema Solar, Estrellas, Galaxias y cosmología, y
   Exploración espacial.** Cada pieza lleva uno y solo uno.
2. **Las etiquetas van al vault como tags anidados bajo `voz-del-cosmos`**,
   que se conserva: [ADR 0011](adr/0011-las-etiquetas-viajan-al-vault.md).
3. **Sin tildes y con ñ**, para que «cosmología» y «cosmologia» sean la misma
   etiqueta. La ñ se queda: sin ella, «año-luz» sería otra palabra.
4. **`formato` y `plataforma` no se editan en la pieza en esta fase.** El
   `formato` tiene pendiente su choque de nombres con el «tipo de pieza» del
   editor ([estados §4](estados-del-flujo.md)), y la `plataforma` importa
   cuando lleguen las métricas.
