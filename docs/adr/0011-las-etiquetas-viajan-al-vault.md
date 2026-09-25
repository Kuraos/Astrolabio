# ADR 0011 — Las etiquetas viajan al vault como tags anidados

- **Fecha**: 2026-09-24
- **Estado**: aceptada
- **Contexto**: criterios Y3 y AA de `docs/fase-5-temas.md`. Cambia lo que
  escribe el exportador ([ADR 0007](0007-como-escribe-astrolabio-en-el-vault.md)).

## Problema

Las piezas ganan etiquetas libres, para saber de qué ha hablado Voz del
Cosmos. En el vault, `tags` es «el único eje transversal que cruza carpetas y
types» (`CLAUDE.md` raíz del vault), y hoy el exportador escribe siempre
`tags: [voz-del-cosmos]`. Había que decidir si las etiquetas entran ahí, cómo,
y qué forma tienen para que Obsidian las reconozca.

## Decisión

### Tags anidados bajo `voz-del-cosmos`

Cada etiqueta sale como `voz-del-cosmos/<etiqueta>`, y `voz-del-cosmos` se
queda:

```yaml
tags:
  - voz-del-cosmos
  - voz-del-cosmos/agujeros-negros
```

En el panel de tags de Obsidian quedan agrupadas bajo el tag que ya existía, y
buscar `tag:voz-del-cosmos` encuentra también las anidadas
([documentación de Obsidian](https://obsidian.md/help/tags)). No se mezclan
con las de los cursos.

### Normalizadas en el servidor, para que sean tags válidos

Obsidian no admite espacios en un tag, ni un tag hecho solo de números, y no
distingue mayúsculas. El servidor normaliza cada etiqueta al guardarla:
minúsculas, espacios y `/` a guiones, fuera lo que no sea letra, número, `_` o
`-`, y sin tildes pero con ñ, para que «cosmología» y «cosmologia» sean la
misma. Una etiqueta que queda vacía, o que es solo números, se rechaza.

La `/` no llega a una etiqueta aunque Obsidian la admita: la jerarquía la pone
el exportador, y es de un solo nivel.

## Alternativas descartadas

- **Sueltas en `tags`**, como `agujeros-negros`. Se cruzarían con las del
  resto del vault: a veces una conexión útil, a menudo ruido, y sin forma de
  saber cuáles son de Voz del Cosmos.
- **Una propiedad aparte**, `etiquetas:`. El panel de tags no la ve y
  consultarla pide Dataview, cuando lo útil de un tag es encontrarlo sin
  escribir una consulta.
- **Conservar las tildes.** Obsidian las admite, pero «cosmología» y
  «cosmologia» serían dos etiquetas, y solo las sugerencias al escribir lo
  evitarían.
- **Quitar también la ñ.** «Año-luz» pasaría a ser otra palabra.

## Consecuencias

- `tags` conserva `voz-del-cosmos`: la nota sigue pasando la auditoría del
  vault, y lo que ya filtraba por ese tag sigue funcionando.
- Cambiar una etiqueta en Astrolabio la cambia en el vault al reexportar,
  porque el exportador reescribe la nota entera (ADR 0007).
- Renombrar un tag en Obsidian no llega a Astrolabio: la dirección es una
  sola ([ADR 0001](0001-fuente-de-verdad-por-type.md)).
