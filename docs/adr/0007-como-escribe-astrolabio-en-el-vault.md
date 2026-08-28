# ADR 0007 — Cómo escribe Astrolabio en el vault

- **Fecha**: 2026-08-27
- **Estado**: aceptada
- **Contexto**: criterios I1–I5 de `docs/fase-1-vault.md`, implementa el ADR 0001.

## Problema

El ADR 0001 decidió *qué* dirección tiene la autoridad. Faltaba decidir *cómo*
se ejerce: con qué nombre se escribe el archivo, hasta dónde llega el permiso
de escritura, y qué pasa cuando la nota generada ya existe.

Tres preguntas con consecuencias, y ninguna se contesta sola.

## Decisión

### El nombre del archivo sale del título

El archivo se llama como el título de la pieza. Johan decide que el título es
estable, y sobre eso se construye.

Pero «estable» no es «inmutable», así que la nota generada lleva
`astrolabio_id` en el frontmatter. Si el título cambia, la exportación
**encuentra la nota anterior por ese identificador y la renombra**, en vez de
dejar una huérfana y crear una segunda. Cuesta seis líneas y evita el único
fallo real de esta decisión: dos notas contradictorias sobre la misma pieza.

### La escritura se acota en el montaje, hasta donde se puede

El contenedor monta `03-Negocios/Voz-del-Cosmos/` en escritura, y encima
`Investigacion/` en **solo lectura**. Ahí es donde el ADR 0001 le da la
autoridad al vault, así que ahí Astrolabio no escribe nunca — y que no pueda
lo impone el sistema de archivos, no la buena voluntad del código.

La primera versión de esta decisión montaba la carpeta entera en solo lectura
y abría solo `Contenido/` y el archivo del MOC. No funciona: Docker crea como
**directorio** cualquier ruta de montaje que falte, así que un despliegue sin
vault configurado terminaba con una carpeta llamada `MOC-VozDelCosmos.md`.

El coste aceptado es que `Bitacora/` y `Compartido-Hermano/` quedan
escribibles para el proceso aunque nada las escriba. La protección que de
verdad importa —§2.5, no tocar el vault personal— la sigue dando el montaje
acotado a esta carpeta: el diario está fuera y es inalcanzable.

### Astrolabio escribe en el MOC, en una sección propia

Decisión de Johan. La nota generada se enlaza desde
`## Piezas (generado por Astrolabio)`, una sección que crea y mantiene la
aplicación y que **no toca ninguna sección escrita a mano**.

Queda registrado que esto puede ser innecesario: el MOC ya rastrea
`Contenido/` con Dataview, y la plantilla de contenido cierra con
`## Relacionado → [[MOC-VozDelCosmos]]`, que ya produce la arista en el grafo
—el grafo de Obsidian no distingue dirección—. La sección añade un índice
legible, no conectividad. Si con el tiempo estorba, quitarla no rompe nada.

### Una nota sin la marca de generada no se toca

Si el archivo de destino existe y **no** lleva
`<!-- generado por Astrolabio — no editar -->`, la exportación se niega y
avisa. Significa que alguien la escribió a mano, y la regla de una sola
dirección del ADR 0001 no autoriza a Astrolabio a decidir que su versión es
la buena.

## Alternativas descartadas

- **Identificador opaco como nombre de archivo** (`pieza-42.md`). Sobrevive a
  cualquier cambio de título, pero deja la carpeta del vault ilegible para un
  humano, y esa carpeta es de Johan antes que de la aplicación.
- **Montar el vault entero en escritura.** Una línea menos en `compose.yaml` a
  cambio de que un fallo cualquiera pueda escribir en el diario personal
  (§2.5). No.
- **Sobrescribir siempre.** Más simple, y convierte cualquier edición manual
  en pérdida silenciosa.

## Consecuencias

- Exportar es **idempotente**: la misma pieza produce el mismo archivo, y
  reexportar lo actualiza en vez de duplicarlo.
- Renombrar una pieza mueve su nota. Los wikilinks que apunten al nombre viejo
  se rompen igual — eso Obsidian lo resuelve al renombrar desde su interfaz, y
  Astrolabio no puede. Es el coste aceptado de nombrar por título.
- El editor no exporta. El destino es el vault personal de Johan, y el ADR
  0001 se lo asigna a él; la comprobación es un 403 en el servidor.
