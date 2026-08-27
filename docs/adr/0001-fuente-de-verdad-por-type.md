# ADR 0001 — Fuente de verdad dividida por `type`

- **Fecha**: 2026-08-26
- **Estado**: aceptada
- **Contexto**: Astrolabio convive con un vault Obsidian personal.

## Problema

El pipeline editorial ya vive en el vault de Johan, versionado en git y
enlazado al respaldo científico. El editor no tiene Obsidian ni debe tener
acceso a ese repositorio. Si ambos sistemas pueden editar lo mismo, hace
falta resolución de conflictos entre dos almacenes de texto.

## Decisión

La autoridad se divide por el campo `type` que el vault ya usa:

| `type` | Fuente de verdad | Quién ve |
|---|---|---|
| `literature` (respaldo científico) | Vault | Solo Johan |
| `permanent` | Vault | Solo Johan |
| `contenido` (piezas) | **Astrolabio** | Los dos |
| `bitacora` del proyecto | Vault | Solo Johan |

Y una **regla de una sola dirección**: `contenido` se edita únicamente en
Astrolabio; el vault recibe una copia exportada, marcada como generada, que
nunca se edita a mano. El respaldo viaja al revés, en solo lectura.

La nota exportada lleva `fuente: astrolabio` en el frontmatter y un
comentario `<!-- generado por Astrolabio — no editar -->`, para que dentro de
seis meses no haya duda de cuál copia es la buena.

## Alternativas descartadas

- **Sincronización bidireccional.** Exige resolución de conflictos real
  sobre texto largo. Es la complejidad que hunde proyectos personales, y el
  beneficio (editar el guion en Obsidian) no lo justifica.
- **Un CMS sobre git (Decap, TinaCMS, Keystatic).** Elegante, pero el
  colaborador necesitaría acceso al repositorio, y `git clone` no tiene
  granularidad de carpeta. Ver ADR 0002 y CLAUDE.md §2.5.
- **Separar `Voz-del-Cosmos/` a su propio repo y compartir ese.** Viable
  técnicamente (`git subtree split`), pero deja el flujo dependiendo de que
  el editor use git, y los submódulos dentro de un vault sincronizado con
  `obsidian-git` son una fuente conocida de fricción.

## Consecuencias

- Johan cambia de hábito: el guion se escribe en Astrolabio, no en Obsidian.
- El grafo, el MOC y las queries Dataview del vault siguen funcionando sin
  cambios, porque la nota generada es indistinguible de una escrita a mano.
- El exportador debe producir frontmatter que pase la auditoría del vault
  sin hallazgos. Eso es un criterio de aceptación, no un detalle.
