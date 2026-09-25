# ADR 0012 — La fecha de publicación viaja al vault

- **Fecha**: 2026-09-24
- **Estado**: aceptada
- **Contexto**: criterios AF de `docs/fase-6-tablero.md`. Cambia lo que
  escribe el exportador ([ADR 0007](0007-como-escribe-astrolabio-en-el-vault.md)),
  como antes el estado ([ADR 0009](0009-el-estado-viaja-al-vault.md)) y las
  etiquetas ([ADR 0011](0011-las-etiquetas-viajan-al-vault.md)).

## Problema

La plantilla `contenido` del vault trae `fecha_publicacion`, y el exportador
la escribe vacía desde la Fase 1: la pieza no tenía ninguna fecha que poner
ahí. El MOC de Voz del Cosmos ordena por ese campo su tabla «Tracking de
contenido» (`SORT fecha_publicacion ASC`), así que hoy esa tabla no ordena
nada.

Con la Fase 6 la pieza gana una fecha de publicación prevista, y la real ya
estaba en la historia: el día del traspaso `publicar`, que es uno solo por
pieza porque de `publicada` no sale nada. Había que decidir cuál de las dos
va al vault.

## Decisión

**La prevista mientras la pieza no está publicada; la real, después.**

| La pieza | `fecha_publicacion` |
|---|---|
| Sin publicar, con fecha prevista | la prevista |
| Sin publicar, sin fecha prevista | vacía, como hoy |
| Publicada | el día del traspaso `publicar` |

Así la tabla del MOC, ordenada por un solo campo, sirve de calendario para lo
que viene y de registro para lo publicado, y `status`, en la columna de al
lado, dice cuál de las dos fechas es.

La real se calcula como `fecha`: en la zona horaria del vault y no en UTC.
`traspaso.creado_en` se guarda en UTC, y una pieza marcada de noche en Bogotá
cae en UTC al día siguiente. Las dos salen sin comillas, como un `date` de
YAML, igual que en la plantilla escrita a mano.

## Alternativas descartadas

- **Solo la real.** Un solo significado, pero la tabla del MOC quedaría vacía
  para todo lo que está en curso, que es lo que un «tracking» quiere ver.
- **Solo la prevista.** Una pieza publicada guardaría en el vault una fecha
  que no ocurrió: el registro mentiría cada vez que el plan se corriera.
- **Dos campos, con la prevista aparte.** Cambia la plantilla del vault, su
  auditoría y la consulta del MOC, para una distinción que `status` ya hace.

## Consecuencias

- La nota envejece hasta la exportación siguiente, como el estado (ADR 0009):
  si la fecha prevista cambia, o la pieza se publica, el vault lo sabe al
  reexportar.
- La fecha real es el día en que se pulsó «Publicar» en Astrolabio. Si se
  marca días después de subir la pieza, el vault dirá el día del clic.
- Una consulta de Dataview que quiera solo fechas reales filtra por
  `status = "publicada"`.
