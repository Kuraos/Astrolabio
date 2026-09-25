# Fase 6 — Tablero, tareas y fechas

**Código terminado el 2026-09-25**, con las decisiones de §7; queda su prueba
de terminado (§5), que se hace en el uso. Resuelve el problema 4 de la
[hoja de ruta](hoja-de-ruta.md), y es la última fase que ella ordena: lo que
venga después saldrá de ese uso, con su propio documento.

## 1. Objetivo

Preparar piezas y ver en qué se trabaja sin tener un Trello aparte.

Johan lo pidió así: «una lista de tareas compartida tipo Trello/checklist para
poder preparar posts, líneas de tiempo y saber en qué se trabaja».

**La advertencia de la hoja de ruta sigue en pie.** Un Trello es alcance
infinito, y en un proyecto de dos personas esta es la fase que se abandona a
la mitad. Entra lo que contesta una de tres preguntas, y nada más:

- **¿Qué me toca y para cuándo?** El tablero, las fechas y las semanas.
- **¿Qué le falta a cada pieza?** La checklist de la pieza.
- **¿Qué hay que hacer que no es de ninguna pieza?** Las tareas sueltas,
  como «comprar el micrófono».

## 2. Fuera de alcance — no implementar

Arrastrar tarjetas: mover una pieza es una transición, con sus reglas y sus
confirmaciones, y se hace dentro de la pieza (§7.4) · asignar tareas a una
persona · fechas en las tareas · editar el texto de una tarea: se borra y se
escribe otra · tareas recurrentes · comentarios en las tareas · colores y
etiquetas en las tarjetas · notificaciones y avisos, también los de fechas
vencidas · un calendario mensual o un diagrama de Gantt: la línea de tiempo es
una lista por semanas · que una tarea pendiente impida un traspaso (§7.2) ·
llevar al vault la fecha de entrega o las tareas · la métrica de atasco del
§2.6 y el panel de métricas.

## 3. El terreno, verificado

Mirado en el código, en la carpeta del vault que lee la app y con Node, el
2026-09-24:

- **El tablero sale de lo que la API ya devuelve.** `GET /api/piezas` trae
  cada pieza con su `estado` y de quién es (K4), y la pantalla principal ya
  las carga todas (`App.tsx`). Cada estado es de un solo rol (`DE_QUIEN_ES`,
  en `models.py`), así que las piezas de una columna comparten turno.
- **La lista de hoy ordena por turno** (N1): primero las de quien mira, y cada
  fila dice de quién es. En el tablero, el orden lo pone el flujo, y el turno
  lo sigue diciendo cada tarjeta.
- **La pieza no tiene más fecha que `creada_en`.** La real de publicación ya
  existe: el `creado_en` del traspaso `publicar`, que es uno solo por pieza
  porque de `publicada` no sale nada.
- **El exportador escribe `fecha_publicacion: null` siempre**, y el MOC del
  vault ordena por ese campo su tabla «Tracking de contenido»
  (`SORT fecha_publicacion ASC`). Hoy esa tabla no ordena nada.
- **`fecha` se exporta en la zona horaria de Johan** (`_fecha_local`):
  `creada_en` se guarda en UTC, y exportarla tal cual adelantaba un día las
  piezas hechas de noche. La fecha real de publicación sale de otra marca en
  UTC y corre el mismo riesgo.
- **En el navegador, `new Date('2026-09-28')` es la medianoche UTC**: en
  Bogotá, las 19:00 del 27, y con día y mes en `es-CO` se lee «27 de sept».
  Comprobado con Node en la zona `America/Bogota`. Una fecha de
  calendario leída así se muestra un día antes, y en una máquina en UTC, como
  la de la CI, el error no se ve.
- **El material ya es el patrón de las tareas.** Los dos roles añaden y
  quitan enlaces, con `creado_por` de la sesión y 401 sin ella
  (`material.py`). Las tareas siguen ese camino y no el de `traspaso`: se
  marcan, se desmarcan y se borran, así que no son historia (§2.6).
- **Ninguna pantalla tiene todavía una casilla ni un campo de fecha.** El
  navegador trae los dos —`<input type="checkbox">` y `<input type="date">`—,
  así que no hace falta ninguna dependencia.
- **La prueba del 401 (C5) recorre el esquema OpenAPI** (`test_piezas.py`):
  los endpoints nuevos quedan cubiertos sin tocarla.
- La última migración es `550cb0579c43`.

## 4. Criterios de aceptación

Las letras siguen después de la AA de la Fase 5.

### AB. El tablero

- **AB1** El tablero reemplaza la lista de piezas y su orden por turno (N1,
  §7.4): una columna por estado, en el orden del flujo —investigación,
  solicitud entregada, material aprobado, finalizada, diseño aprobado y
  publicada (§7.8)—, con las palabras de
  [estados-del-flujo.md](estados-del-flujo.md) (N4). Las columnas vacías
  también se ven.
- **AB2** Repartir las piezas en columnas es una función pura, con sus pruebas
  en vitest. Una pieza con un estado que el cliente no conoce sale en una
  columna propia con su identificador, en vez de desaparecer: feo, pero no
  invisible, como `enPalabras`.
- **AB3** Cada tarjeta lleva el título, de quién es el turno —resaltado cuando
  le toca a quien mira, como hoy en la lista— y «sin guion» si no lo tiene. Al
  pulsarla se abre la pieza, donde están los botones para moverla.
- **AB4** El filtro por etiqueta del catálogo (Z2) filtra el tablero, y también
  las semanas (AE2) desde el 2026-09-25, a pedido de Johan.
- **AB5** El tablero ocupa 1024 px, el ancho de la pieza abierta (X1). En una
  pantalla estrecha, las columnas se apilan en el orden del flujo.

### AC. Las fechas

- **AC1** `pieza` gana `fecha_entrega` y `fecha_publicacion_prevista`, en su
  propia migración: fechas de calendario (`DATE`), sin hora ni zona, y nulas
  mientras no se decidan.
- **AC2** Los dos roles las cambian por `PATCH`, como el resto de la pieza
  (§7.5), y un `null` la borra. Lo que no sea una fecha, 422.
- **AC3** En la vista de la pieza, dos campos de fecha del navegador, «Entrega
  del diseño» y «Publicación prevista» (§7.7), que se guardan al cambiarlos,
  sin pasar por «Guardar», como el tema (Y5).
- **AC4** La tarjeta del tablero muestra las fechas que tenga la pieza, con día
  y mes, mientras sigan pendientes: la entrega, hasta que el editor finaliza la
  pieza, y la publicación prevista, hasta que se publica. Después, la entrega
  ya no dice nada y la prevista se leería como la real, que es otra (cambiado
  el 2026-09-25, a pedido de Johan).
- **AC5** El cliente lee `AAAA-MM-DD` como un día del calendario, nunca con
  `new Date(texto)` (§3). Lo vigila una prueba en vitest que corre en la zona
  de Bogotá también en la CI, porque en UTC el error no se ve.

### AD. Las tareas

- **AD1** Una tabla `tarea`, en su propia migración: el texto, si está hecha,
  quién la marcó y cuándo, quién la creó y cuándo, y la pieza, que es
  opcional: sin pieza, la tarea es suelta (§7.1). Quién marca y quién crea
  salen de la sesión, nunca del cuerpo (M1). Desmarcarla borra quién la marcó.
- **AD2** `GET /api/tareas` devuelve todas, las de las piezas y las sueltas: el
  tablero cuenta las de cada pieza y la pantalla principal muestra las
  sueltas, así que basta un pedido. `POST` la crea, con pieza o sin ella;
  `PATCH` la marca o la desmarca; `DELETE` la quita. Un texto vacío es 422, y
  una pieza que no existe, 404.
- **AD3** Los dos roles hacen todo eso con cualquier tarea, como con el
  material, con su prueba por acción y por rol. Sin sesión, 401 (C5).
- **AD4** En la vista de la pieza, un panel «Tareas», en orden de llegada: cada
  una con su casilla, que se guarda al marcarla, y las hechas dicen quién las
  marcó. Un campo para añadir y una × para quitar, como las etiquetas.
- **AD5** En la pantalla principal, debajo del tablero, el mismo panel con las
  tareas sueltas.
- **AD6** La tarjeta del tablero dice cuántas tareas le quedan a la pieza, de
  cuántas.
- **AD7** El panel del traspaso dice cuántas quedan, junto a los botones, y no
  los desactiva; el servidor tampoco lo comprueba. La checklist informa y no
  bloquea (§7.2).

### AE. Las semanas

- **AE1** Una función pura, con sus pruebas en vitest, agrupa por semana, de
  lunes a domingo (§7.6), las fechas que siguen pendientes: la entrega de cada
  pieza que el editor aún no ha finalizado —en investigación, solicitud
  entregada o material aprobado— y la publicación prevista de cada pieza sin
  publicar.
- **AE2** En la pantalla principal, debajo del tablero, un panel «Semanas» con
  esas semanas en orden, y en cada una sus entradas por fecha: el día, si es
  entrega o publicación, y la pieza, que se abre al pulsarla. La semana en
  curso se señala, y las anteriores con algo pendiente también salen, antes
  que ella: son lo atrasado.

### AF. El vault

- **AF1** El exportador escribe en `fecha_publicacion` la fecha prevista
  mientras la pieza no está publicada, y la real —el día del traspaso
  «Publicar», en la zona horaria del vault, como `fecha`— cuando ya lo está
  ([ADR 0012](adr/0012-la-fecha-de-publicacion-viaja-al-vault.md)). Sin
  ninguna de las dos, vacía, como hoy.
- **AF2** Como `fecha`, sin comillas: un `date` de YAML. La nota sigue pasando
  la auditoría del vault (I3).

## 5. Definición de terminado

**El editor abre Astrolabio desde su máquina y sabe, sin preguntar, qué piezas
le tocan y para cuándo tiene que entregarlas. Johan ve en el tablero qué le
falta a cada pieza y marca las tareas que va cumpliendo, y después de exportar,
la tabla «Tracking de contenido» del MOC muestra la fecha prevista de lo que
viene y la real de lo publicado.** Ninguno de los dos abrió un Trello.

## 6. Orden sugerido

Cada paso sirve por sí solo: si la fase se detiene a la mitad, lo hecho se usa.

1. El tablero, con lo que la API ya devuelve (AB). No toca el servidor.
2. Las fechas, en la base, en la pieza y en la tarjeta (AC).
3. Las tareas: la tabla y sus endpoints con sus pruebas (AD1–AD3), y después
   la pieza, las sueltas, la tarjeta y el traspaso (AD4–AD7).
4. Las semanas (AE).
5. El vault (AF).

## 7. Decisiones — acordadas el 2026-09-24

1. **Hay tareas sueltas, en una lista aparte.** La pieza de una tarea es
   opcional.
2. **Una tarea pendiente no impide mover la pieza.** La checklist informa y no
   bloquea: que bloquee se decide cuando el hábito exista, como dice la
   [guía de la conversación](conversacion-estados-guia.md) sobre los estados.
3. **`fecha_publicacion` es la prevista hasta publicar, y la real después**:
   [ADR 0012](adr/0012-la-fecha-de-publicacion-viaja-al-vault.md). La columna
   `status`, al lado en el MOC, dice cuál de las dos es.
4. **El tablero reemplaza la lista, y la tarjeta abre la pieza.** Mover sigue
   siendo cosa de la pieza, donde ya están los botones, la nota de «Devolver»
   y las confirmaciones: llevarlos a cada tarjeta sería repetirlos.

Y cuatro que no hizo falta preguntar, y que se cambian si no convencen:

5. **Los dos roles cambian las fechas y las tareas**, como el resto de la
   pieza y el material. Ninguna regla nueva de quién puede qué.
6. **La semana va de lunes a domingo.**
7. **En pantalla, «Entrega del diseño».** «Fecha de entrega» es palabra del
   editor ([estados §1](estados-del-flujo.md)), pero junto al botón
   «Entregar» de Johan, que es la otra entrega, se leería al revés.
8. **Las publicadas tienen su columna.** Sin ella, una pieza publicada solo se
   encontraría por sus etiquetas. La columna crecerá; cuando estorbe, se
   recorta.
