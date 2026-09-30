# Fase 10 — Dónde se atasca, copias y aviso

**Aprobada el 2026-09-29**, con todas las decisiones de §7. Nace de que
las fases 2 a 8 quedaron aprobadas con el editor y de tres huecos que el PRD ya
nombraba: la métrica de §8.2, que se registra y no se ve; la copia de
seguridad, que [ARCHITECTURE §8](ARCHITECTURE.md) dice que nadie programa; y el
aviso de «te toca», que las fases 2, 6 y 7 dejaron fuera a propósito.

## 1. Objetivo

Tres cosas, cada una con su razón:

- **Ver dónde se atasca una pieza.** Es la métrica que ninguna herramienta
  comprada da (§2.6): cuánto tarda cada etapa. Los datos ya están en la tabla
  `traspaso`; falta una pantalla.
- **No perder la historia.** Esa misma tabla es «la mitad del valor del
  producto» (§2.3), y hoy vive en un volumen de Docker sin copia.
- **Enterarse de que te toca sin preguntar.** El objetivo del producto es que
  dejen de mandarse mensajes; si nadie se entera de que le pasaron la pieza,
  el mensaje vuelve.

## 2. Fuera de alcance — no implementar

Avisos fuera de la app —correo, `ntfy`, push del navegador— (§7.6) · medias,
medianas o cualquier agregado de tiempos, y ordenar temas por tiempo (§7.4) ·
el panel de métricas de plataforma del PRD §8.3 · copias hacia otra máquina o
a la nube, y cifrarlas (§7.5) · restaurar desde la app · distinguir lo nuevo de
lo antiguo en el aviso (§7.7) · los bocetos de short y de video largo
([fase 11](fase-11-guion-grafico.md)) · alertas de «lleva demasiado atascada»:
la pantalla muestra los días, y qué es demasiado lo decide quien mira.

## 3. El terreno, verificado

Mirado en el código el 2026-09-29:

- **`traspaso` tiene lo que hace falta**: `pieza_id`, `transicion`, `desde`,
  `hacia`, `creado_por`, `creado_en`, y es de solo inserción por un trigger
  (ADR 0008). La pieza tiene `creada_en`. De ahí sale cuánto estuvo una pieza
  en cada estado: de un traspaso al siguiente.
- **`creado_en` es `now()` de Postgres, la hora en que empezó la transacción**,
  no la de la escritura. Dos traspasos de una misma pieza se serializan con
  `FOR UPDATE`, así que el segundo puede haber empezado antes de que el primero
  terminara: por eso la historia se ordena por `id` y no por hora
  (`traspasos.py`, M3). Una duración entre dos traspasos puede salir de unos
  milisegundos negativa.
- **`GET /api/piezas` no trae los traspasos**, y pedirlos pieza a pieza es un
  pedido por cada una: la pantalla necesita un endpoint propio.
- **La pieza abierta es una copia aparte** (`abierta`, en `App.tsx`): `cargar`
  reemplaza `piezas` y `tareas` pero no la toca. Recargar cada tanto no pisa
  lo que se escribe en el guion.
- **`cargar` hoy muestra el error y borra el tablero** si un pedido falla
  (`setError` reemplaza la pantalla). Sirve para una acción del usuario; con una
  recarga automática, un corte de un minuto lo dejaría en blanco.
- **El título de la pestaña es fijo** (`web/index.html`) y ningún código lo
  cambia. El conteo de «Te toca» está escrito en línea en `App.tsx`.
- **`respaldo` ya significa otra cosa en este repo**: el respaldo científico
  del vault (`respaldo.py`). La copia de la base se llama **copia**, en código
  y en pantalla.
- **La imagen de Postgres ya está fijada por digest** (ADR 0013). Usarla para
  el servicio de copias garantiza que `pg_dump` sea de la misma versión que el
  servidor, que es lo que `pg_dump` exige.
- **Docker está en esta máquina** (29.7.2): las copias se pueden probar de
  verdad, con restauración incluida.

## 4. Criterios de aceptación

Las letras siguen después de la AW de la Fase 9.

### AX. Dónde se atasca

- **AX1** `GET /api/atasco` devuelve, por pieza, su id, su título, su estado,
  si está publicada, los días que estuvo o lleva en cada estado, su ciclo y
  cuántas veces la devolvieron o reformularon. Los dos roles pueden; sin
  sesión, 401.
- **AX2** El tiempo en un estado va de un traspaso al siguiente, empezando en
  `creada_en` para el primero y terminando en el momento de la consulta para el
  estado actual (la publicación cierra la cuenta: de `publicada` no sale
  nada). Es una función pura, con sus pruebas en pytest sobre historias
  armadas a mano.
- **AX3** Si la pieza vuelve a un estado —«Devolver», «Reformular»—, ese
  tiempo se suma al del estado, y la devolución se cuenta aparte. La suma de
  las etapas es siempre el tiempo entre `creada_en` y ahora (o la publicación).
- **AX4** Ninguna duración sale negativa: la diferencia entre dos `creado_en`
  se acota en cero (§3). Una prueba lo fuerza con marcas invertidas.
- **AX5** El ciclo de una pieza va de su **primer** traspaso `entregar`
  —«solicitud entregada», lo más parecido al «guion cerrado» del §2.6— hasta
  `publicar`. Una pieza que nunca se entregó no tiene ciclo; una en curso lo
  tiene abierto, hasta ahora.
- **AX6** Una estación «Atasco» en la pantalla principal, debajo de «Semanas»,
  con dos listas y sin agregados (§7.4):
  - **En curso**: las piezas sin publicar, la que lleva más días en su estado
    actual primero. Cada una dice su título, su estado, de quién es y cuántos
    días lleva ahí.
  - **Publicadas**: cada una con su ciclo en días y una barra partida por
    etapas, con el estado escrito en cada tramo, no solo el color.
  Pulsar una pieza la abre. El filtro por etiqueta (AB4) también filtra esta
  estación.
- **AX7** Los días se leen como «hoy», «1 día» y «N días», y una pieza sin
  datos dice «sin entregar». Es una función pura, con vitest.

### AY. Las copias

- **AY1** Un servicio `copias` en compose, con la imagen de Postgres ya fijada
  por digest, que hace `pg_dump -Fc` de la base al arrancar y cada
  `COPIAS_CADA_HORAS` horas (24 por defecto), en
  `astrolabio-AAAAMMDD-HHMMSS.dump`. Guarda las últimas `COPIAS_GUARDAR`
  (14 por defecto) y borra las demás.
- **AY2** La copia se escribe con un nombre provisional y se renombra al
  terminar, y las viejas solo se borran si la nueva salió bien. Una copia a
  medias nunca cuenta como copia, ni hace perder la anterior.
- **AY3** La carpeta del PC donde caen es `COPIAS_HOST_PATH`, con `./copias`
  por defecto —ignorada por git—, para que un `.env` anterior arranque igual,
  como con Syncthing. `.env.example` documenta las tres variables. La contraseña
  de la base llega por el entorno, sin ningún literal (§2.4).
- **AY4** El servicio tiene su `healthcheck`: sano si hay una copia de menos de
  dos periodos. Si `pg_dump` falla, `docker compose ps` lo muestra como no
  sano y `docker compose logs copias` dice por qué. No tumba la app.
- **AY5** **Se probó restaurar**, no solo copiar: una copia real se restaura en
  una base vacía y coinciden los conteos de `pieza`, `traspaso`, `tarea` y
  `boceto` con los de la base viva; y sobre la restaurada, un `UPDATE` de
  `traspaso` sigue fallando, o sea, el trigger del ADR 0008 sobrevive. El
  procedimiento queda en ARCHITECTURE §8.
- **AY6** [ADR 0017](adr/0017-copias-de-la-base.md): dónde caen, cada cuánto,
  qué contienen —hashes de contraseña y sesiones, así que son tan sensibles
  como la base— y lo que no cubren: si `COPIAS_HOST_PATH` está en el mismo
  disco, un disco muerto se lleva la base y las copias. Apuntarla a otra unidad
  es decisión de Johan.

### AZ. El aviso de «te toca»

- **AZ1** El título de la pestaña es `(N) Astrolabio`, con N las piezas que le
  tocan a quien mira, y `Astrolabio` a secas con cero. El conteo es el mismo
  del bloque naranja, sacado a una sola función pura para que no se escriba
  dos veces.
- **AZ2** La lista se recarga cuando la pestaña vuelve a estar visible y cada
  60 segundos mientras lo está. Nada más se sondea, y con la pestaña oculta no
  hay pedidos.
- **AZ3** Una recarga automática que falla no borra el tablero ni pone un
  error: se queda lo último bueno y lo intenta en el siguiente turno. Los
  errores de las acciones de quien usa la app siguen como estaban (D4).
- **AZ4** La recarga no pisa la pieza abierta ni lo que se escribe en ella: se
  comprueba mirándolo, con un guion con texto sin guardar y una recarga en
  medio.
- **AZ5** El aviso solo funciona con la pestaña abierta, y la documentación lo
  dice (§7.6). Con la pestaña cerrada no hay aviso.

### BA. Los documentos

- **BA1** El PRD, `ARCHITECTURE.md` —§8 con las copias, y el aviso—, el README,
  `AGENTS.md` y `DESIGN_SYSTEM.md`, al día. La barra partida por etapas es un
  patrón nuevo y se documenta allí antes de repetirse (§4).
- **BA2** La lista de comandos de `AGENTS.md` §5 gana los de las copias: ver
  el estado, forzar una y restaurar.

## 5. Definición de terminado

**Johan abre «Atasco» y ve, de una pieza publicada, cuántos días estuvo en cada
etapa, y de las que van en curso cuál lleva más tiempo donde está. Una copia
real de la base se restauró en una base vacía y contó lo mismo. Con la pestaña
del editor abierta y oculta, su título pasa a `(1) Astrolabio` cuando Johan
entrega una pieza.** En el código: `npm --prefix web run check` y
`docker compose run api pytest` en verde, y la estación mirada a 1280 y a
375 px.

## 6. Orden sugerido

Cada paso sirve por sí solo: si la fase se detiene a la mitad, lo hecho se usa.

1. Las copias (AY). Protegen lo que ya existe y no dependen de nada.
2. El endpoint del atasco, con su función pura y sus pruebas (AX1–AX5).
3. La estación del atasco (AX6, AX7).
4. El aviso (AZ).
5. Los documentos (BA).

## 7. Decisiones — acordadas con Johan el 2026-09-29

Al elegir el alcance:

1. **Entra el atasco, las copias y el aviso.**
2. **El aviso es solo dentro de la app**, sin servicio externo.
3. **Las copias caen en una carpeta del PC, fuera de Docker.**

Y las que se propusieron con el documento, aprobadas con él:

4. **Sin agregados en el atasco.** Con pocas piezas publicadas una mediana de
   tiempo por etapa mide el azar, como el ranking de temas del ADR 0004. Se
   muestra cada pieza con sus días; cuando haya suficientes publicadas, un
   resumen es una decisión nueva.
5. **`COPIAS_CADA_HORAS=24` y `COPIAS_GUARDAR=14`.** Un guion se escribe en
   horas y la base es pequeña (ADR 0003): una copia diaria y dos semanas de
   historia pesan poco. Cambian por el `.env`.
6. **Nada de avisos fuera de la app.** Es el techo de lo elegido: si el editor
   deja la pestaña cerrada, no se entera. Si en el uso resulta poco, el
   siguiente paso es un servicio externo con su ADR, como el 0016.
7. **El contador no distingue lo nuevo.** `(2)` dice cuántas te tocan, no
   cuántas llegaron desde tu última visita. Marcarlas como nuevas pide
   recordar qué vio cada quien; se añade si el contador no alcanza.
8. **«Copia» y no «respaldo»**, porque `respaldo` ya es el científico del
   vault.
9. **Los bocetos de short y video largo son la Fase 11**, aparte de esta: qué
   lleva un guion gráfico no está dicho, y la §2.8 pide que salga de las
   palabras del editor antes de modelar nada.
