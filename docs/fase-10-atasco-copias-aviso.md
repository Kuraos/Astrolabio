# Fase 10 — Dónde se atasca, copias y aviso

**Código terminado el 2026-09-30**, con todas las decisiones de §7; queda su
prueba de terminado (§5) en el uso, y que Johan elija dónde caen las copias en
su `.env`. Nace de que
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

- **AX1** `GET /api/atasco` devuelve, por pieza, su id, los segundos que
  estuvo en cada estado, los que lleva en el de ahora —o nada si ya se
  publicó—, su ciclo y cuántas veces la devolvieron y cuántas la
  reformularon. El título, el estado y el turno ya los trae `/api/piezas`, y
  el cliente los junta por id (§8). Los dos roles pueden; sin sesión, 401.
- **AX2** El tiempo en un estado va de un traspaso al siguiente, empezando en
  `creada_en` para el primero y terminando en el momento de la consulta para el
  estado actual (la publicación cierra la cuenta: de `publicada` no sale
  nada). Es una función pura, con sus pruebas en pytest sobre historias
  armadas a mano.
- **AX3** Si la pieza vuelve a un estado —«Devolver», «Reformular»—, ese
  tiempo se suma al del estado, y la devolución se cuenta aparte. La suma de
  las etapas es siempre el tiempo entre `creada_en` y ahora (o la publicación).
- **AX4** Ninguna duración sale negativa (§3), y la suma de AX3 sigue
  siendo exacta: cada tramo se cuenta desde la marca más alta vista hasta
  ahí, no desde la del traspaso anterior (§8). Una prueba lo fuerza con
  marcas invertidas.
- **AX5** El ciclo de una pieza va de su **primer** traspaso `entregar`
  —«solicitud entregada», lo más parecido al «guion cerrado» del §2.6— hasta
  `publicar`. Una pieza que nunca se entregó no tiene ciclo; una en curso lo
  tiene abierto, hasta ahora.
- **AX6** Una estación «Atasco» en la pantalla principal, debajo de «Semanas»,
  con dos listas y sin agregados (§7.4):
  - **En curso**: las piezas sin publicar, la que lleva más días en su estado
    actual primero. Cada una dice su título, su estado, de quién es y cuántos
    días lleva ahí.
  - **Publicadas**: una fila por pieza con una columna por etapa —los días y
    una barra proporcional— y su ciclo, con el nombre de cada etapa escrito,
    no solo el color (§8).
  Pulsar una pieza la abre. El filtro por etiqueta (AB4) también filtra esta
  estación.
- **AX7** Los días se leen como «menos de 1 día», «1 día» y «N días», los
  enteros que caben (§8). Es una función pura, con vitest.

### AY. Las copias

- **AY1** Un servicio `copias` en compose, con la imagen de Postgres ya fijada
  por digest, que cada hora mira si la última copia tiene más de
  `COPIAS_CADA_HORAS` horas (24 por defecto) y, si la tiene, hace un
  `pg_dump -Fc` de la base en `astrolabio-AAAAMMDD-HHMMSS.dump`, con la hora en
  UTC (§8). Guarda las últimas `COPIAS_GUARDAR` (14 por defecto) y borra las
  demás. Sin las filas de `sesion` (§8).
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

## 8. Lo que apareció por el camino

### Las copias

- **Las copias no llevan las sesiones.** El `id` de `sesion` es la cookie tal
  cual (ADR 0006): con esas filas, una copia dejaría entrar como cualquiera de
  los dos. `pg_dump --exclude-table-data=sesion` copia la tabla vacía, y
  restaurar cuesta volver a entrar. Comprobado: la base viva tenía dos
  sesiones y la restaurada, ninguna.
- **Mirar cada hora en vez de copiar al arrancar y dormir un periodo.** Con
  14 copias guardadas, catorce reinicios en un día habrían borrado las dos
  semanas de historia; y un PC apagado tres días no copiaría hasta un día
  después de encenderlo. Ahora un reinicio no copia si la última es reciente,
  y el PC que vuelve copia enseguida.
- **`COPIAS_GUARDAR=0` habría borrado la copia recién hecha.** El script
  rechaza cualquier valor que no sea un entero desde 1, y no arranca.
- **`restaurar` se niega si la base de destino tiene tablas.** Es la orden
  que se teclea en el peor día, y no puede pisar la base viva por un nombre
  equivocado. Después de perder el volumen, la base que crea Postgres está
  vacía y se restaura en ella: el orden está en ARCHITECTURE §8.
- **Git habría convertido el script a CRLF** en Windows (`core.autocrlf`), y
  `sh` lee el `\r` como parte de cada orden. `.gitattributes` fija LF en los
  `.sh`.
- **La CI copia y restaura en cada push**, y comprueba el mensaje del trigger
  del ADR 0008 en la restaurada, no solo que el `DELETE` falle: sin la base,
  psql también fallaría y la prueba pasaría sin comprobar nada.
- **Probado el 2026-09-29 en una pila aparte**, con piezas, traspasos, tareas,
  usuarios y sesiones: los conteos, un guion con LaTeX y una nota con ñ salen
  iguales; el trigger rechaza `UPDATE` y `DELETE` en la restaurada; un reinicio
  no copia; con `COPIAS_GUARDAR=2` quedan dos; un `pg_dump` con la contraseña
  mala no deja parcial ni borra nada; la salud es mala sin copias o con una de
  hace tres días.

### El atasco

- **Contar desde la marca más alta, no desde la anterior.** Acotar cada tramo
  en cero, como decía AX4, dejaba de restar tiempo pero lo inventaba: tras un
  traspaso con marca invertida, el siguiente tramo empezaba antes y la suma
  pasaba de la vida de la pieza. Contando desde el máximo visto, cada tramo es
  cero o más y la suma sale exacta. La prueba de las marcas invertidas falla
  si se quita.
- **La API devuelve solo los tiempos.** El título, el estado, el turno y las
  etiquetas ya llegan con `/api/piezas`, en el mismo turno de carga; repetirlos
  sería otra forma de que se separen.
- **Columnas por etapa en lugar de una barra partida.** Con una barra por
  pieza, comparar el tramo del medio entre dos piezas es adivinar; con una
  columna por etapa, en cuál se tarda se lee hacia abajo. Sin colores por
  etapa, que la paleta no tiene (DESIGN_SYSTEM §1): cada columna lleva su
  nombre y una barra en `control`, medida contra la etapa más larga de la
  lista.
- **«Menos de 1 día», no «hoy».** Una pieza que llegó anoche lleva menos de un
  día, pero llegó ayer. «Sin entregar» no hizo falta: las en curso muestran lo
  que llevan en su estado, y toda publicada pasó por una entrega.
- **Mientras carga, «Cargando…».** La estación se pinta antes de que lleguen
  las piezas, y decía «Todavía no hay piezas.». Se vio en la primera captura.
- **Los días, primero en la fila.** Al final de una fila de 1440 px quedaban
  lejos del título; delante, como la fecha en la lista de semanas, se leen de
  un vistazo y ordenados.
- **Mirado el 2026-09-29** en una pila aparte, con dos piezas publicadas y
  cinco en curso de historias escritas a mano —una devuelta y reformulada—, a
  1280 y a 375 px, como Johan y como el editor, sin desborde horizontal: los
  días de cada etapa cuadran con las historias, y el editor lee «Te toca» solo
  en la suya y nunca «editor».

### El aviso

- **La vigilancia de la pestaña es una función aparte**, `recargarMientrasSeVe`
  en `pestana.ts`, que recibe el documento: vitest corre sin navegador, y así
  se prueba con uno de mentira y el reloj de vitest que oculta no pide nada y
  que al volver pide enseguida. Quitarle la condición de visibilidad hace
  fallar dos pruebas.
- **El conteo sale de `cuantasTeTocan`**, en `flujo.ts`: el bloque naranja y
  el título no pueden decir cosas distintas.
- **Un techo conocido**, con su comentario `ponytail:` en `App.tsx`: una
  recarga que salió antes de marcar una tarea puede volver después y
  enseñarla sin marcar hasta la siguiente. En la base está bien. Si se ve en
  el uso, se descarta la respuesta de una recarga que empezó antes del último
  cambio.
- **Probado el 2026-09-30 en un navegador de verdad**, contra la pila aparte,
  con el reloj de Playwright para no esperar minutos: el editor entra con
  `(1) Astrolabio`; Johan, desde su sesión, le aprueba el material de otra
  pieza, y al minuto el título pasa a `(2)` sin que nadie recargue; oculta,
  diez minutos sin un pedido, y al volver, uno enseguida; con `/api/piezas`
  cortado, la recarga falla sin aviso y el tablero y el título se quedan; con
  una pieza abierta, el guion y la nota del traspaso a medio escribir siguen
  igual tras la recarga, y «Sin guardar» también.
- **Mirar la captura destapó un fallo de la prueba, no de la app**: el primer
  campo de la pieza es la nota del traspaso, no el guion, y la primera versión
  del script escribía ahí. Ahora escribe en los dos.
