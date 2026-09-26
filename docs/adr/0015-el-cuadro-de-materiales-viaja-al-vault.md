# ADR 0015 — El cuadro de materiales viaja al vault

- **Fecha**: 2026-09-26
- **Estado**: aceptada
- **Contexto**: criterios AQ de `docs/fase-8-cuadro-de-materiales.md`. Cambia
  lo que escribe el exportador ([ADR 0007](0007-como-escribe-astrolabio-en-el-vault.md)),
  como antes el estado ([ADR 0009](0009-el-estado-viaja-al-vault.md)), las
  etiquetas ([ADR 0011](0011-las-etiquetas-viajan-al-vault.md)) y la fecha de
  publicación ([ADR 0012](0012-la-fecha-de-publicacion-viaja-al-vault.md)).

## Problema

La Fase 8 le da a la pieza lo que pide el cuadro de materiales del editor:
tipo de pieza, propósito, nivel, destino, el copy de cada lámina y el
caption. La nota del vault es la copia de la pieza (ADR 0001), y una copia
que deja fuera la mitad del cuadro no sirve de registro.

Tres de esos datos ya estaban en el frontmatter y cambian de forma:
`formato` cambia de valores y `plataforma` pasa de texto a lista. Eso rompe
lo que en el vault dependa de los valores viejos.

## Decisión

**Todo el cuadro viaja, con los identificadores de la base, como el estado.**

| En la pieza | En la nota |
|---|---|
| `formato` | `formato:`, con los valores nuevos (`short`, `video_largo`…) |
| `proposito`, `nivel` | `proposito:` y `nivel:`, detrás de `formato` |
| `plataforma` | `plataforma:` como lista de YAML, vacía si no hay |
| `copy_grafico` | `## Copy gráfico`, un `### Lámina N` por lámina |
| `caption` | `## Caption`, el texto tal cual |

Las dos secciones van después de `## Guion`, en el orden en que se trabajan.
Sin contenido, salen con el encabezado y vacías, como el respaldo: la
estructura de la nota no depende de lo que esté relleno.

Los identificadores y no las palabras, por lo mismo que el estado (ADR
0009): una consulta de Dataview que filtre por `formato = "short"` no se
rompe si mañana la pantalla dice «Reel» otra vez.

## Alternativas descartadas

- **Solo el frontmatter, sin los textos.** Los copys son parte del trabajo de
  Johan, y el vault es donde guarda lo que escribe. Dejarlos solo en la base
  los haría depender de que Astrolabio siga existiendo.
- **`plataforma` como texto separado por comas.** Evita cambiar el tipo, pero
  Dataview trata una lista de YAML como lista y una cadena con comas como una
  cadena: `contains(plataforma, "tiktok")` solo funciona con la lista.
- **Mantener los valores viejos de `formato` en el vault y traducir al
  exportar.** Dos vocabularios para lo mismo, y el viejo es justo el que el
  editor no usa.

## Consecuencias

- La plantilla `_Templates/Contenido-VozDelCosmos.md` y cualquier consulta
  que filtre por los valores viejos de `formato` o trate `plataforma` como
  texto dejan de coincidir. Astrolabio no las toca (AGENTS §2.5); las
  actualiza Johan a mano.
- Las notas exportadas antes de la fase conservan los valores viejos hasta
  que se reexporten.
- La nota crece con el copy y el caption, que envejecen hasta la exportación
  siguiente, como el guion.
