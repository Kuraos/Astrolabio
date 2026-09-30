#!/bin/sh
# Las copias de la base (Fase 10, AY; ADR 0017). Lo corre el servicio `copias`
# de compose, con la misma imagen que `db`:
#
#   (sin argumentos)        vigila: cada hora mira si la última copia tiene más
#                           de COPIAS_CADA_HORAS y, si la tiene, hace otra
#   una                     hace una copia ahora y termina
#   sana                    el healthcheck: hay una copia de menos de dos periodos
#   restaurar ARCHIVO BASE  restaura ARCHIVO, de la carpeta de copias, en BASE,
#                           que tiene que estar vacía o no existir
#
# La conexión llega por el entorno de libpq —PGHOST, PGUSER, PGPASSWORD y
# PGDATABASE—, que pone compose: aquí no hay ninguna credencial (§2.4).

set -u

DIR=/copias
CADA=${COPIAS_CADA_HORAS:-24}
GUARDAR=${COPIAS_GUARDAR:-14}

# Con GUARDAR=0, rotar borraría también la copia recién hecha.
for n in "$CADA" "$GUARDAR"; do
  case $n in
    '' | *[!0-9]* | 0*)
      echo "copias: COPIAS_CADA_HORAS y COPIAS_GUARDAR son enteros desde 1" >&2
      exit 2
      ;;
  esac
done

# Hay una copia de menos de $1 minutos.
reciente() {
  find "$DIR" -maxdepth 1 -name 'astrolabio-*.dump' -mmin "-$1" | grep -q .
}

una() {
  # En UTC, como guarda Postgres las horas: el nombre ordena por fecha.
  nombre="astrolabio-$(date -u +%Y%m%d-%H%M%S).dump"
  parcial="$DIR/.$nombre.parcial"

  # AY2: con un nombre que ninguna otra parte cuenta como copia hasta que
  # pg_dump termina bien. Un corte a la mitad deja un archivo oculto, nunca
  # una copia rota con cara de buena.
  #
  # Sin las filas de `sesion`: su `id` es la cookie tal cual (ADR 0006), y una
  # copia con ellas dejaría entrar como Johan o como el editor a quien la
  # tenga. Restaurar cuesta volver a entrar, nada más.
  if ! pg_dump --format=custom --exclude-table-data=sesion --file="$parcial"; then
    rm -f "$parcial"
    echo "copias: pg_dump falló; las anteriores siguen ahí" >&2
    return 1
  fi
  mv "$parcial" "$DIR/$nombre"
  echo "copias: $nombre"

  # Las viejas se borran solo ahora, con la nueva ya en su sitio.
  ls "$DIR"/astrolabio-*.dump | sort -r | tail -n "+$((GUARDAR + 1))" | xargs -r rm -f
}

vigilar() {
  # Mirar cada hora en vez de dormir un periodo entero: reiniciar el PC no
  # gasta copias, y un PC que estuvo apagado tres días copia al volver.
  while :; do
    reciente $((CADA * 60)) || una
    sleep 3600
  done
}

restaurar() {
  if [ $# -ne 2 ]; then
    echo "uso: restaurar ARCHIVO BASE" >&2
    return 2
  fi
  archivo="$DIR/$1"
  base=$2
  if [ ! -f "$archivo" ]; then
    echo "copias: no está $1 en la carpeta de copias" >&2
    return 1
  fi

  # Si ya existe, no pasa nada: la vacía que crea Postgres con el volumen
  # nuevo es justo donde se restaura después de perderlo.
  createdb "$base" 2>/dev/null
  tablas=$(psql --dbname="$base" --tuples-only --no-align \
    --command="SELECT count(*) FROM pg_tables WHERE schemaname = 'public'") || return 1
  if [ "$tablas" != 0 ]; then
    echo "copias: $base ya tiene tablas; solo se restaura en una base vacía" >&2
    return 1
  fi

  # Todo o nada: una restauración a medias sería peor que ninguna.
  pg_restore --exit-on-error --single-transaction --dbname="$base" "$archivo"
}

case ${1:-} in
  '') vigilar ;;
  una) una ;;
  sana) reciente $((2 * CADA * 60)) ;;
  restaurar) shift; restaurar "$@" ;;
  *)
    echo "uso: copias.sh [una | sana | restaurar ARCHIVO BASE]" >&2
    exit 2
    ;;
esac
