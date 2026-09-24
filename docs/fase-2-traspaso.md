# Fase 2 — El traspaso

**Cerrada el 2026-09-21**, con las decisiones de §7; su prueba con el editor
(§5) se hace en el uso. Implementa [estados-del-flujo.md](estados-del-flujo.md),
el resultado del §2.8. El alcance vigente está en [`AGENTS.md`](../AGENTS.md)
§7.

## 1. Objetivo

Que cada pieza diga sola en qué estado está y de quién es, para que ninguno de
los dos tenga que preguntárselo al otro.

Es el centro del §1: el problema que resuelve Astrolabio no es gestionar
contenido, es el traspaso, y la prueba de que funciona es que dejen de
mandarse mensajes sobre el estado de las piezas.

La Fase 0 demostró que el sistema se atraviesa entero; la 1, que convive con el
vault. Esta es la primera que hace lo que el producto promete, y su riesgo ya
no es técnico sino de modelo: una máquina de estados que no describe el
trabajo real hace que la aplicación **mienta** sobre dónde está cada pieza.

## 2. Fuera de alcance — no implementar

Los campos del cuadro de materiales —propósito, tamaño, el «formato» del
editor, fecha de entrega— y la checklist que los exigiría · archivos:
Syncthing, rutas y comprobación de llegada (ADR 0003); mientras tanto, el
archivo viaja como hoy · miniaturas · versiones de pieza · comentarios más allá
de la nota del traspaso (§7.2) · avisos y notificaciones · pasos propios de
Johan dentro de `investigación` · lotes o bloques de piezas · métricas y APIs
de plataforma (ADR 0004).

**Tampoco se bloquea la edición según el estado.** La pieza se sigue editando
como hoy: el estado dice de quién es el turno, no quién puede escribir. Si hace
falta cerrarla, será porque el uso lo pidió, con su propia decisión.

## 3. El terreno, verificado

No son suposiciones; están mirados en el código y en el vault:

- `pieza` no tiene `estado`, y cinco sitios lo dicen a propósito: los
  docstrings del módulo `models.py` y de `Pieza`, el de `PiezaPublica` en
  `piezas.py`, la migración `7390a2fd6023` y
  `test_la_pieza_no_tiene_campo_estado`, que lo afirma. Los sostenía el §2.8,
  y la condición ya se cumplió con [estados-del-flujo.md](estados-del-flujo.md).
  Esta fase corrige los que describen el presente. La migración se queda como
  está: es historia, y lo que anunciaba —«llegarán en su propia migración
  cuando ocurra»— es justo lo que pasa ahora.
- La autorización de piezas se decide con `_solo_investigador`. Las
  transiciones necesitan reglas en los dos sentidos: hay pasos que solo puede
  dar el editor.
- `PATCH /api/piezas/{id}` deja a los dos roles editar todo menos `respaldo`.
  No cambia en esta fase.
- El exportador escribe `status: "idea"` fijo, con el comentario «cuando los
  estados existan, saldrán de aquí».
- En el vault, `status` es obligatorio para `type: contenido`, pero ni la
  plantilla ni el `CLAUDE.md` de la carpeta fijan sus valores: la plantilla solo
  trae `idea`. El MOC ya agrupa las piezas con `GROUP BY status`.
- La prueba de C5 recorre el esquema OpenAPI, así que un endpoint nuevo queda
  cubierto por el 401 sin tocarla.
- La última migración es `7390a2fd6023`.

## 4. Criterios de aceptación

### K. El estado

- **K1** `pieza` gana `estado`, en su propia migración. Las piezas que ya
  existen y las que se creen empiezan en `investigación` (§7.1).
- **K2** Los valores son exactamente los de
  [estados-del-flujo.md §2](estados-del-flujo.md#2-estados). En el código y en
  la base, estados y transiciones van en minúscula, sin tildes y con guion bajo
  (`diseno_aprobado`, `aprobar_diseno`); en pantalla, las palabras del
  documento (N4). `test_la_pieza_no_tiene_campo_estado` se retira y la
  reemplaza una que fija ese conjunto: añadir un estado obliga a pasar por el
  documento, que es la forma que tiene el §2.8 de seguir vigente.
- **K3** `estado` no se cambia por `PATCH`. Solo un traspaso lo mueve.
- **K4** La API devuelve, con cada pieza, su estado, de quién es y qué
  transiciones puede dar quien pregunta. El cliente no deduce nada de eso: la
  tabla de transiciones vive en un solo sitio, el servidor.

### L. Las transiciones

- **L1** Un solo endpoint mueve la pieza: `POST /api/piezas/{id}/traspasos`,
  con el nombre de la transición y el estado desde el que se mueve. Las
  transiciones son las de
  [estados-del-flujo.md §3](estados-del-flujo.md#3-transiciones), nombradas
  con los verbos de sus propias frases: «entregar» (P4), «aprobar el
  material» (P3), «devolver», «finalizar» (P4), «aprobar el diseño» (P10),
  «publicar» (P11) y «reformular».
- **L2** Cada regla de un solo rol tiene su prueba de 403, con la cookie del
  otro rol y directamente contra la API: entregar, aprobar el diseño, publicar
  y devolver una pieza finalizada son de Johan; finalizar y devolver una
  solicitud, del editor. Seis pruebas. Y como en C2, un 403 no deja rastro: ni
  cambia el estado ni escribe `traspaso`.
- **L3** Las dos que puede dar cualquiera —aprobar el material y reformular—
  tienen su prueba con cada rol.
- **L4** Si la pieza ya no está en el estado desde el que se pidió moverla
  —porque el otro la movió antes, o porque la pantalla era vieja—, o si esa
  transición no sale de ese estado, **409** y no se escribe nada. Dos personas
  escribiendo a la vez es la razón por la que el §3 eligió Postgres; aquí es
  donde se nota.
- **L5** Cambiar el estado y escribir el traspaso ocurren en la misma
  transacción: no existe una pieza que cambió de estado sin su fila, ni una fila
  sin su cambio.

### M. `traspaso`

- **M1** Cada transición inserta una fila con la pieza, la transición, el
  estado de origen y el de destino, quién la dio, cuándo y una nota opcional
  (§7.2). Quién sale de la sesión, nunca del cuerpo de la petición, igual que
  `creada_por`.
- **M2** Es append-only (§2.6) y lo impone la base: un trigger rechaza
  `UPDATE`, `DELETE` y `TRUNCATE`
  ([ADR 0008](adr/0008-traspaso-append-only-en-la-base.md)). La prueba lo
  intenta por SQL y espera el rechazo de Postgres, no el del código.
- **M3** Los dos roles leen la historia entera de una pieza, en orden.

### N. Interfaz

- **N1** La lista de piezas muestra el estado y de quién es cada una, y primero
  las que son de quien mira. Es el «cuadro de solicitud» del editor, «para
  mantener el flujo de las piezas a desarrollar» (P1).
- **N2** La pieza ofrece solo los botones de las transiciones que la API dice
  que el usuario puede dar ahora — **además** del 403 del servidor, nunca en su
  lugar, como en D3.
- **N3** La pieza muestra su historia: cada traspaso con quién, cuándo y su
  nota, si la tiene.
- **N4** En pantalla se leen las palabras de
  [estados-del-flujo.md](estados-del-flujo.md), no los identificadores del
  código.

### O. El vault

- **O1** El exportador escribe en `status` el estado que tiene la pieza al
  exportar, con el mismo identificador de la base, en vez de `idea` fijo
  ([ADR 0009](adr/0009-el-estado-viaja-al-vault.md)). La nota sigue pasando la
  auditoría del vault (I3).

## 5. Definición de terminado

**Una pieza recorre el flujo entero entre los dos, cada uno en su máquina:
Johan la entrega, aprueban el material, el editor la finaliza, Johan la
devuelve con una nota que dice qué ajustar, el editor la vuelve a finalizar, y
Johan aprueba el diseño y la publica.** En ningún momento alguno de los dos
tuvo que escribirle al otro para saber en qué iba, y la historia de la pieza
muestra cada paso con quién y cuándo.

Como en la Fase 0, no cuenta en la máquina de quien lo programó: la prueba es
el editor, desde la suya.

## 6. Orden sugerido

1. La migración: `estado` en `pieza` y la tabla `traspaso` con su nota y su
   trigger (K1, M1, M2).
2. Las transiciones en el servidor, con todas sus pruebas (L), antes de
   cualquier botón.
3. Lo que la API devuelve para la interfaz (K4, M3).
4. Interfaz (N).
5. Vault (O).

## 7. Decisiones — acordadas el 2026-09-21

1. **La etapa inicial se llama `investigación`.** El nombre es de Johan,
   porque la etapa es suya (estados §6.3).
2. **El traspaso lleva una nota libre, opcional.** `devolver` es «se aplican
   ajustes», y sin decir cuáles, cada devolución terminaría en un mensaje de
   «¿qué ajusto?», justo el que el §1 quiere eliminar. Los comentarios
   completos siguen fuera (§2).
3. **El exportador escribe el estado en `status`**, con el mismo identificador
   de la base: [ADR 0009](adr/0009-el-estado-viaja-al-vault.md). El vault no
   fija valores para ese campo y el MOC ya agrupa por él.
4. **Append-only por trigger de Postgres**:
   [ADR 0008](adr/0008-traspaso-append-only-en-la-base.md). Lo garantiza la
   base, para el código de hoy y el que venga.
