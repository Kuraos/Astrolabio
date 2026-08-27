# Fase 1 — La fuente de verdad dividida

**Propuesta de alcance.** Implementa el [ADR 0001](adr/0001-fuente-de-verdad-por-type.md).
Nada entra aquí hasta que este documento esté acordado, igual que en la Fase 0.

## 1. Objetivo

Que el guion se escriba en Astrolabio y llegue al vault sin que nadie copie y
pegue, y que el respaldo científico viaje al revés, en solo lectura.

Dos direcciones, cada una de un solo sentido:

| `type` | Manda | Astrolabio |
|---|---|---|
| `literature` | Vault | **lee**, nunca escribe |
| `contenido` | Astrolabio | **escribe** una copia marcada como generada |

La Fase 0 demostró que el sistema se atraviesa entero. Esta demuestra que
**convive con el vault sin pelearse con él**: el riesgo ya no es la red, es que
dos almacenes de texto se pisen.

## 2. Fuera de alcance — no implementar

Estados y máquina de estados · checklist de traspaso · comentarios · versiones
de pieza · miniaturas · Syncthing y rutas de material (ADR 0003) · métricas y
APIs de plataforma (ADR 0004) · sincronización bidireccional de nada.

El §2.8 sigue vigente sin excepción: `pieza` **continúa sin campo `estado`**.
Esta fase no lo necesita, y esa es parte de su gracia.

## 3. El terreno, verificado

No son suposiciones; están mirados en el vault:

- `03-Negocios/Voz-del-Cosmos/Contenido/` — destino del exportador. **Vacío.**
- `03-Negocios/Voz-del-Cosmos/Investigacion/Recursos/` — origen del respaldo.
  Dos notas `literature` hoy.
- `_Templates/Contenido-VozDelCosmos.md` — el contrato que debe cumplir lo
  exportado: `formato`, `tema`, `status`, `plataforma`, `investigacion[]`,
  `metricas{}`, `tags`, y las secciones `## Respaldo científico`, `## Guion`,
  `## Verificación antes de publicar`, `## Notas de producción`,
  `## Relacionado`.
- La carpeta tiene `CLAUDE.md` propio y **sus reglas mandan dentro de su
  alcance**, incluida la de enlazar cada nota nueva desde `MOC-VozDelCosmos`.

## 4. Criterios de aceptación

### F. Migraciones — primero, y no es negociable

CLAUDE.md §4: «Alembic desde la Fase 1. Dejarlo para después significa no
hacerlo». Va antes que el dominio porque esta fase **cambia el esquema**, y
retrofitear migraciones sobre tablas ya crecidas es el trabajo que nadie hace.

- **F1** `create_all` desaparece de `main.py` y de `seed.py`. El esquema se
  crea únicamente con `alembic upgrade head`.
- **F2** Desde una base vacía, `alembic upgrade head` produce exactamente el
  esquema actual, y `alembic check` no detecta deriva entre modelos y
  migraciones.
- **F3** La CI corre las migraciones antes de las pruebas.

### G. Respaldo científico, en solo lectura

- **G1** La aplicación lista las notas `literature` de `Investigacion/Recursos/`
  con `fuente_titulo`, `autor` y `fecha` leídos del frontmatter real.
- **G2** Un test comprueba que **ninguna ruta de código escribe** bajo la
  carpeta del vault salvo `Contenido/`. Es la mitad del ADR 0001 y la que no
  se nota hasta que ya se rompió algo.
- **G3** La aplicación no lee **nada** fuera de `03-Negocios/Voz-del-Cosmos/`
  (§2.5). Un intento de salirse con `../` falla y queda cubierto por un test.
- **G4** Sin `VAULT_CONTENIDO_PATH` configurada, o apuntando a algo que no
  existe, la aplicación **arranca y funciona igual**, y lo dice en la interfaz.
  El vault es de Johan; el taller no puede depender de que esté montado.

### H. La pieza crece

- **H1** `pieza` gana `guion` (markdown), `formato`, `tema` y `plataforma`.
  **Sigue sin `estado`.**
- **H2** El guion conserva **LaTeX real** en un viaje completo —guardar, leer,
  exportar— sin escapar ni normalizar `$...$` ni `$$...$$`. El contenido lleva
  fórmulas y el vault tiene Latex Suite; romperlas es corromper la pieza.
- **H3** Una pieza referencia notas `literature`, y esa referencia es la que
  alimenta `investigacion:` y `## Respaldo científico` al exportar.
- **H4** El `editor` **no** ve el respaldo científico: el ADR 0001 se lo
  asigna a Johan. Endpoint con 403 y su test, como manda §2.3.

### I. Exportador — una sola dirección

- **I1** Exportar una pieza produce un `.md` en `Contenido/` con el frontmatter
  completo de la plantilla.
- **I2** La nota lleva `fuente: astrolabio` y
  `<!-- generado por Astrolabio — no editar -->`.
- **I3** La nota generada **pasa la auditoría del vault sin hallazgos**. El ADR
  0001 dice literalmente que esto es criterio de aceptación y no un detalle.
- **I4** Reexportar la misma pieza **sobrescribe su copia** y no crea una
  segunda. Un exportador que duplica es peor que no tenerlo.
- **I5** El exportador no escribe **fuera** de `Contenido/`, y nunca toca una
  nota que no lleve la marca de generada. Si el archivo existe y **no** tiene
  la marca, se niega y avisa: alguien lo escribió a mano.

### J. Interfaz

- **J1** Editor de markdown con vista previa y KaTeX.
- **J2** El respaldo disponible se ve al lado del guion, en solo lectura, y se
  puede enlazar a la pieza.
- **J3** Exportar es una acción explícita con resultado visible: qué archivo se
  escribió y dónde.

## 5. Definición de terminado

**Johan escribe un guion con fórmulas en Astrolabio, lo exporta, abre Obsidian,
y la nota está ahí: bien formada, enlazada al respaldo, indistinguible de una
escrita a mano salvo por la marca de generada.** Y la auditoría del vault no
tiene nada que decir sobre ella.

## 6. Orden sugerido

1. **Alembic (F).** Antes de tocar el modelo.
2. Lector de `literature` (G) — solo lectura, el riesgo más bajo.
3. La pieza crece (H), con la prueba de ida y vuelta de LaTeX.
4. Exportador (I).
5. Interfaz (J).

## 7. Decisiones abiertas — a acordar antes de F

Cuatro, y ninguna es de implementación:

1. **¿Qué `status` lleva la nota exportada?** La plantilla trae `status: idea`
   y la pieza no tiene estado (§2.8). Lo más honesto es escribir siempre
   `idea` y dejar que el `status` real llegue cuando exista la máquina de
   estados. Alternativa: no escribir el campo, y que la auditoría se queje.
2. **¿El exportador actualiza `MOC-VozDelCosmos.md`?** La regla del vault
   exige enlazar cada nota nueva desde el MOC para que aparezca en el grafo.
   Cumplirla implica que Astrolabio escriba en un segundo archivo; no
   cumplirla deja una nota huérfana y un paso manual.
3. **¿Exportar es manual o automático?** Un botón es predecible; automático al
   guardar es cómodo y escribe en tu vault sin que lo pidas.
4. **¿El nombre del archivo?** El título de la pieza puede cambiar, y renombrar
   la nota rompería los wikilinks que apunten a ella. Un identificador estable
   los preserva a costa de un nombre de archivo feo.

La 2 y la 4 tienen consecuencias y pedirían ADR corto antes de implementarlas.
