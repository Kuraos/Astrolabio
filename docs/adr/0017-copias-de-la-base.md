# ADR 0017 — Las copias de la base, en una carpeta del PC

- **Fecha**: 2026-09-29
- **Estado**: aceptada
- **Contexto**: criterios AY de `docs/fase-10-atasco-copias-aviso.md`. Toca
  el [ADR 0003](0003-binarios-fuera-de-la-app.md), que contaba con que la base
  cabe en un `pg_dump`, y el [ADR 0008](0008-traspaso-append-only-en-la-base.md),
  porque la historia que protege solo vale si sobrevive.

## Problema

Todo lo que Astrolabio sabe vive en el volumen `db-data` de Docker: las
piezas, sus guiones y la historia de cada traspaso, que es «la mitad del valor
del producto» (AGENTS §2.3). Nada lo copiaba. Restaurar Docker Desktop a
fábrica, o un `docker compose down -v` tecleado de más, lo borra entero, y la
historia no se puede reconstruir de ningún otro sitio.

## Decisión

**Un servicio `copias` en compose hace un `pg_dump` de la base a una carpeta
del PC, fuera de Docker, y guarda las últimas.**

- **La misma imagen que `db`**, por un ancla de YAML: `pg_dump` exige ser de
  la versión del servidor, y así un solo digest mueve las dos (ADR 0013).
- **Cuándo.** Cada hora mira si la última copia tiene más de
  `COPIAS_CADA_HORAS` (24) y, si la tiene, hace otra. Reiniciar el PC no gasta
  copias, y un PC que estuvo apagado copia al volver. Se guardan
  `COPIAS_GUARDAR` (14).
- **Dónde.** `COPIAS_HOST_PATH`, `./copias` por defecto, ignorada por git.
- **Formato `custom`** de `pg_dump`: comprimido, y `pg_restore` lo restaura
  en una transacción.
- **Una copia a medias no cuenta.** Se escribe con un nombre oculto y se
  renombra al terminar; las viejas se borran solo después.
- **Sin las sesiones.** El `id` de `sesion` es la cookie tal cual
  (ADR 0006): una copia con esas filas dejaría entrar como cualquiera de los
  dos. Se copia la tabla vacía; restaurar cuesta volver a entrar.
- **Restaurar solo en una base vacía.** `copias.sh restaurar` se niega si la
  base de destino tiene tablas: la orden no puede pisar la base viva por un
  descuido.
- **Probado restaurando**, no solo copiando, y la CI lo repite en cada push:
  una copia que nunca se restauró es una suposición.

## Alternativas descartadas

- **Un volumen de Docker para las copias.** Muere con lo mismo que mata a
  `db-data`, que es justo de lo que hay que protegerse.
- **Una tarea programada de Windows.** Funciona solo en el PC de Johan, fuera
  del repositorio, y no la levanta `docker compose up` en otra máquina. La
  regla de AGENTS §4 es que la app corra igual en cualquier sitio.
- **Una carpeta sincronizada con la nube.** Cubriría también un disco muerto,
  pero sacaría del PC los hashes de las contraseñas, y el ADR 0002 deja la app
  sin nube. Si Johan la quiere, es cambiar `COPIAS_HOST_PATH`: la decisión es
  suya y está en el `.env`.
- **WAL y recuperación a un instante (PITR).** Es la herramienta para bases
  con escrituras continuas; aquí, dos personas y una copia al día.
- **Excluir `usuario`.** Los hashes son Argon2, y sin la tabla restaurar
  obligaría a volver a sembrar los usuarios y rompería los `creado_por` de la
  historia.

## Consecuencias

- **Una copia es tan privada como la base** menos las sesiones: lleva los
  guiones, la historia y los hashes Argon2 de las contraseñas.
- **No cubre un disco muerto** si `COPIAS_HOST_PATH` está en el mismo disco
  que Docker. Apuntarla a otra unidad es cambiar una línea del `.env`.
- **Se pierde, como mucho, un periodo**: lo escrito desde la última copia.
- **Un servicio más en `docker compose up`**, que no tumba la app si falla:
  nadie depende de él. Su salud la dice `docker compose ps`.
- **`.gitattributes` fija LF en los `.sh`**: con `core.autocrlf` en Windows,
  el script llegaría al contenedor con CRLF y `sh` no lo entendería.
