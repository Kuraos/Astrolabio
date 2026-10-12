# ADR 0019 — Astrolabio crea notas de respaldo, y nada más

- **Fecha**: 2026-10-11
- **Estado**: aceptada
- **Contexto**: criterios BB de `docs/fase-12-fuentes-y-archivo.md`. Enmienda
  el [ADR 0001](0001-fuente-de-verdad-por-type.md), que le daba al vault toda
  la autoridad sobre `literature` y a Astrolabio solo la lectura, y con él el
  §2.1 de `AGENTS.md`.

## Problema

Para respaldar una pieza con una fuente nueva, Johan tenía que salir de la
pieza, abrir Obsidian, crear la nota en `Investigacion/Recursos/` con su
frontmatter, volver y pulsar «Actualizar». Lo encontró difícil y poco claro:
el sitio donde se necesita la fuente no era el sitio donde se podía añadir.

La regla que lo impedía existe por una razón que sigue en pie: dos sistemas
editando el mismo texto piden resolución de conflictos.

## Decisión

**Astrolabio puede crear una nota `literature`. No la edita, no la renombra y
no la borra: desde que nace, la nota es del vault.**

Lo que el ADR 0001 quería evitar es que dos sistemas editen lo mismo. Crear un
archivo que no existe no es editar: no hay versión anterior con la que chocar.
La autoridad sobre el contenido no cambia de manos.

- **Solo el `investigador`**, con su 403 para el editor (§2.3).
- **Solo en `Investigacion/Recursos/`**, que se monta en escritura encima de
  un `Investigacion/` que sigue en solo lectura.
- **Nunca pisa.** El archivo se abre en modo `x`, que falla si ya existe: la
  API responde 409 y pide otro nombre. Lo decide el sistema de archivos, sin
  una comprobación previa que pudiera llegar tarde.
- **En su propio módulo**, `fuentes.py`. `respaldo.py` sigue siendo el que
  lee, con su prueba de que no escribe; `fuentes.py` tiene la suya, de que
  solo crea.
- **Con la forma que pide el vault**: el frontmatter y las secciones del
  `CLAUDE.md` de la carpeta, para que la nota sea indistinguible de una hecha
  a mano. Sin marca de generada: no es una copia, es el original.

## Alternativas descartadas

- **Un botón que abra Obsidian** con la nota preparada. No tocaba la regla,
  pero deja el trabajo donde estaba: en otra ventana.
- **Una referencia en la pieza, sin nota.** Un DOI pegado no pasa por el
  vault, no sirve a otra pieza y no lleva nivel de confianza, que es lo que
  Voz del Cosmos exige de cada fuente.
- **Editar la nota desde Astrolabio.** Es la sincronización en dos sentidos
  que el ADR 0001 prohíbe, y lo sigue prohibiendo.

## Consecuencias

- **El §2.1 cambia de «nunca lo escribe» a «lo crea y no lo vuelve a tocar».**
  Proponer que Astrolabio edite una nota sigue siendo romper la invariante.
- **Lo que protege al vault ya no es el montaje**, que ahora deja escribir en
  `Recursos/`, sino el modo `x` y una prueba. Es una protección más débil que
  la anterior, y es el precio.
- **Una nota a medias llega al vault.** Sin resumen nace con
  `status: por-leer`; terminarla sigue siendo trabajo de Obsidian.
- **El nivel de confianza es obligatorio** en el formulario: una fuente no
  entra sin decir si es consenso, hipótesis o resultado preliminar.
- **Si `Recursos/` no existe**, Docker la crea vacía al montar.
