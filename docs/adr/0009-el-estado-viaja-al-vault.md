# ADR 0009 — El estado viaja al vault en `status`

- **Fecha**: 2026-09-21
- **Estado**: aceptada
- **Contexto**: criterio O1 de `docs/fase-2-traspaso.md`. Amplía el ADR 0007 y
  sustituye la decisión 7.1 de `docs/fase-1-vault.md`.

## Problema

Las notas `type: contenido` del vault exigen `status`. La Fase 1 escribía
siempre `idea` porque la pieza no tenía estado, y lo dejó así «hasta que
exista la máquina de estados». Ya existe.

Quedan dos preguntas: si el vault refleja el estado, y con qué valores.

## Decisión

El exportador escribe en `status` el estado de la pieza en el momento de
exportar, con **el mismo identificador que guarda la base**, sin traducirlo:
`investigacion`, `solicitud_entregada`, `material_aprobado`, `finalizada`,
`diseno_aprobado`, `publicada`.

Sin traducción, por dos razones. El vault no fija valores para `status`: ni la
plantilla ni el `CLAUDE.md` de la carpeta los enumeran, y la auditoría solo
exige que el campo exista. Y ya usa identificadores en minúscula y sin tildes
(`idea`, `leido`). Una tabla que tradujera los estados a otro vocabulario
sería un segundo sitio donde viven, y el criterio K2 existe para que haya uno.

El MOC ya agrupa las piezas con `GROUP BY status`, así que Obsidian muestra el
flujo sin que se toque una línea del vault.

## Alternativas descartadas

- **Seguir escribiendo `idea`.** Era honesto mientras no había estados; ahora
  es un dato falso en cada nota, y el `GROUP BY status` del MOC se queda con un
  solo grupo.
- **Un vocabulario propio del vault** (`idea`, `en producción`, `publicado`).
  Es inventar una segunda máquina de estados, que es lo que el §2.8 prohíbe,
  solo que en otro sitio.
- **Reexportar en cada traspaso**, para que el vault esté siempre al día.
  Escribe en el vault personal de Johan sin que lo pida, y la Fase 1 eligió
  que exportar sea una acción explícita (J3).

## Consecuencias

- **El `status` de la nota es el del momento de exportar** y envejece hasta la
  exportación siguiente, igual que el guion. El vault es una copia; la verdad
  sigue en Astrolabio (ADR 0001).
- Si un estado cambia de nombre, las notas exportadas antes conservan el viejo
  hasta que se reexporten.
- Una pieza en su etapa inicial exporta `status: investigacion` junto al campo
  `investigacion:` con sus fuentes. Son dos campos que comparten palabra y no
  chocan.
- La nota sigue pasando la auditoría del vault (I3): cambia el valor de un
  campo que ya existía, no el contrato.
