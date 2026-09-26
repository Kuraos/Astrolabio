# Fase 8 — El cuadro de materiales

**Alcance vigente desde el 2026-09-26**, con todas las decisiones de §7 y §8
acordadas con Johan. Es alcance nuevo, como la Fase 7: nace de la prueba de
Johan del 2026-09-25, no de la [hoja de ruta](hoja-de-ruta.md).

## 1. Objetivo

Que la pieza lleve lo que el editor pide en su cuadro de materiales
([estados §4](estados-del-flujo.md)), con sus palabras, para que al llegar a
`solicitud entregada` no tenga que preguntar qué es, para qué es, dónde va ni
qué texto lleva cada lámina.

Del cuadro, la pieza ya tiene el tipo (mal nombrado: `formato`) y un
`plataforma` que ninguna pantalla deja rellenar. Le faltan el propósito, el
nivel y los textos: el copy de cada lámina y el caption de la publicación.
Las quejas del editor sobre las solicitudes que llegaban «listas» son de esos
textos: «copys excesivamente largos», «textos con errores de ortografía»,
«ideas no concretas que no tienen una finalidad». Esta fase no corrige la
ortografía ni juzga la idea, pero sí pone el largo a la vista y obliga a
decir la finalidad en una palabra.

Cierra la pregunta 4 de [estados §6](estados-del-flujo.md) y la primera del
[PRD §11](PRD.md): los «copys in graphic» son un texto aparte del guion. Y la
tercera: la palabra «formato» sale de la pantalla y queda «tipo de pieza».

## 2. Fuera de alcance — no implementar

Añadir fuentes de respaldo desde la app (sigue saliendo del vault, AGENTS
§2.1) · los bocetos con Claude (fase propia, después de esta) · corregir la
ortografía · bloquear un traspaso porque falte algo del cuadro · el tamaño en
píxeles o en papel («formato y tamaño» del cuadro, §8.6) · rankings por
propósito o nivel (AGENTS §2.7) · publicar en las redes o leer sus métricas ·
tocar la plantilla del vault (§6).

## 3. El terreno, verificado

Mirado en el código el 2026-09-26:

- **`formato` acepta `reel`, `carrusel`, `video` y `post`** (`Formato`, en
  `piezas.py`), y el comentario dice que son «los cuatro que pregunta la
  plantilla del vault». Ninguna pantalla lo edita: `Pieza.tsx` solo lo
  muestra, junto al tema y la plataforma.
- **`plataforma` es una cadena libre** (`String(50)`), sin lista y sin
  campo en el cliente. Lo que haya en la base solo pudo llegar por la API a
  mano.
- **Los dos roles editan la pieza** (`PATCH`, `piezas.py`); solo el respaldo
  es de Johan. Los campos nuevos siguen esa regla.
- **El exportador escribe `formato` y `plataforma` en el frontmatter** tal
  cual están en la base. Cambiar sus valores cambia lo que ven las consultas
  de Dataview del vault.
- **Los identificadores de la base van en minúsculas y sin tildes**
  (`material_aprobado`), y el cliente los pone en palabras con `enPalabras`
  (`flujo.ts`). Los valores nuevos siguen el mismo patrón.
- **El ADR 0004 cuenta las celdas tema × formato × plataforma.** Con
  propósito y nivel dentro, cada celda se partiría en diez y ninguna llegaría
  a `n` en años.

## 4. Criterios de aceptación

Las letras siguen después de la AM de la Fase 7.

### AN. Los datos

- **AN1** `formato` pasa a `carrusel`, `post_individual`, `short`, `poster` y
  `video_largo`. Una migración de Alembic convierte los que hay: `reel` →
  `short`, `video` → `video_largo`, `post` → `post_individual`; `carrusel` se
  queda.
- **AN2** `proposito` (nuevo, uno por pieza): `divulgar`, `promocionar`,
  `educar`, `noticia`, `comunidad`.
- **AN3** `nivel` (nuevo, uno por pieza): `basico`, `avanzado`.
- **AN4** `plataforma` pasa a ser una lista (§8.1): `instagram`, `tiktok`,
  `youtube`, `impreso`. La migración convierte los valores que reconoce, sin
  distinguir mayúsculas; si encuentra otro, **se detiene** y dice cuál, en vez
  de perderlo.
- **AN5** `copy_grafico` (nuevo): una lista de textos, uno por lámina (§8.2).
  `caption` (nuevo): un texto.
- **AN6** Todos opcionales y todos editables por los dos roles. La API
  rechaza con 422 un valor fuera de las listas, como hoy con `formato` y
  `tema`; y el cliente toma las listas de un solo sitio, como `TEMAS` en
  `api.ts`.

### AO. En la pieza

- **AO1** La estación del tema se amplía con el cuadro: tipo de pieza,
  propósito, nivel y destino, con esas palabras. Ninguna pantalla dice
  «formato».
- **AO2** Junto a la estación, lo que falta del cuadro, en una línea:
  «Falta: propósito, destino». Es información, no un candado: el traspaso no
  cambia (§2).

### AP. Los textos, junto al guion

- **AP1** La estación del guion tiene tres pestañas: «Guion», «Copy gráfico»
  y «Caption». La barra de herramientas y la vista previa solo están en
  «Guion».
- **AP2** «Copy gráfico» muestra un campo por lámina, numerado, con su
  recuento de caracteres y de palabras debajo, y botones para añadir, quitar
  y mover láminas. Un «Post individual» o un «Póster» empiezan con una.
- **AP3** «Caption» cuenta caracteres y hashtags. Si la pieza tiene destinos,
  muestra el límite de cada uno junto al recuento, sacado de una sola tabla
  en el cliente (§8.3). Pasarse lo marca en rosa; no impide guardar.
- **AP4** Las funciones que cuentan caracteres, palabras y hashtags son puras
  y llevan sus pruebas en vitest. Un emoji cuenta como un carácter, que es
  como lo cuentan las redes, no como dos unidades de UTF-16.

### AQ. El vault

- **AQ1** El exportador escribe `proposito` y `nivel` en el frontmatter,
  detrás de `formato`, y `plataforma` como lista de YAML
  ([ADR 0015](adr/0015-el-cuadro-de-materiales-viaja-al-vault.md)).
- **AQ2** Después de `## Guion`, dos secciones: `## Copy gráfico`, con un
  `### Lámina N` por lámina, y `## Caption`. Sin copy o sin caption, la
  sección sale vacía, como hoy el respaldo.

### AR. Las pruebas y los documentos

- **AR1** Pytest: la migración de AN1 y AN4 en los dos sentidos, el 422 de
  cada lista, el editor editando los campos nuevos y la nota exportada con
  todo lo de AQ.
- **AR2** `DESIGN_SYSTEM.md` documenta las pestañas, que son un patrón nuevo
  (AGENTS §4). El PRD, `ARCHITECTURE.md`, `estados-del-flujo.md` §6 y
  `AGENTS.md` §7, al día.

## 5. Definición de terminado

**El editor abre una pieza en `solicitud entregada` y no tiene que preguntar
de qué tipo es, para qué es, dónde va ni qué dice cada lámina.** Lo ha hecho
con una pieza real. En el código: `npm --prefix web run check` y
`docker compose run api pytest` en verde, y la pieza mirada a 1280 y a
375 px.

## 6. Lo que no hace Astrolabio y debe hacer Johan

La plantilla `_Templates/Contenido-VozDelCosmos.md` del vault tiene la lista
vieja de formatos y no tiene `proposito` ni `nivel`. Astrolabio no la toca
(AGENTS §2.5: no lee ni escribe fuera de la carpeta de Voz del Cosmos, y la
plantilla es de Johan). Hay que actualizarla a mano cuando la fase se
fusione, junto con cualquier consulta de Dataview que filtre por
`formato = "reel"` o trate `plataforma` como texto.

## 7. Decisiones — acordadas con Johan el 2026-09-25 y 26

1. **El respaldo sigue saliendo del vault.** No se añaden fuentes desde la
   app (AGENTS §2.1, ADR 0001).
2. **«Tipo de pieza» es el `formato` del código**: Carrusel, Post
   individual, Short, Póster, Video largo.
3. **«Propósito»**: Divulgar, Promocionar, Educar, Noticia, Comunidad.
4. **«Nivel», campo aparte**: Básico, Avanzado.
5. **«Destino»**: Instagram, TikTok, YouTube, Impreso. Lo que va a TikTok se
   publica tal cual en Instagram. Impreso es a largo plazo, si se ve viable
   hacer mercancía: entra en la lista para no migrar otra vez.
6. **Copy gráfico y caption, junto al guion, en pestañas.**
7. **Al vault**, con su ADR.

## 8. Propuestas — aprobadas por Johan el 2026-09-26

1. **Destino es una lista, no un valor.** Si lo de TikTok va también a
   Instagram, una sola plataforma obligaría a escoger una o a duplicar la
   pieza. Cuesta cambiar `plataforma` en el frontmatter de texto a lista.
2. **El copy gráfico es una lista de láminas**, no un texto con separadores.
   El largo se cuenta por lámina, que es donde el editor lo sufre, y los
   bocetos de la fase siguiente necesitan saber qué texto va en cada una. En
   un Short o un Video largo, cada «lámina» es un rótulo en pantalla.
3. **Los límites del caption viven en una tabla del cliente** y se comprueban
   en la documentación de cada plataforma el día que se escriban, no de
   memoria: cambian (Instagram, por ejemplo, ha recortado los hashtags
   admitidos). Impreso no tiene caption.
4. **Sin límite para el copy gráfico** hasta que el editor diga uno: se
   muestran los recuentos y él juzga. Inventar un umbral sería decidir por
   él qué es «excesivamente largo».
5. **Propósito y nivel no entran en las celdas del ADR 0004.** Se guardan y
   se exportan; el panel de métricas, cuando llegue, no los cruza.
6. **«Formato y tamaño» queda fuera.** Casi siempre se deduce del tipo y el
   destino (un Short es vertical), y el tamaño del impreso no se sabe hasta
   que exista. Si el editor lo echa en falta, se añade como un campo más.
7. **Tipo de pieza y destino no se validan entre sí.** Un Póster en TikTok
   es raro, pero la regla que lo prohíba la tendría que dictar el editor.

## 9. Orden sugerido

1. Los datos y su migración (AN), con sus pruebas.
2. El vault (AQ): el exportador sabe escribir lo nuevo antes de que haya
   pantalla para rellenarlo.
3. La pieza (AO).
4. Las pestañas (AP).
5. Los documentos (AR2).
