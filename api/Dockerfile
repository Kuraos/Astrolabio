# Por digest, como todas las imágenes base (ADR 0013): el tag dice qué línea se
# sigue y el digest, en qué punto de ella. Docker solo usa el digest.
FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Genera constraints.txt; la imagen de la api no pasa por aquí (ADR 0013):
#
#   docker build --no-cache --target lock --output api api
#
# Resuelve requirements.txt desde cero, sin el lock anterior: regenerarlo no
# puede depender de que el viejo todavía se instale. Sin `--no-cache`, con
# requirements.txt intacto, devolvería el lock que ya estaba en la caché.
FROM base AS resolucion
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && { echo '# Lock de la api: todas las versiones que instala la imagen (ADR 0013).'; \
      echo '# Regenerar: docker build --no-cache --target lock --output api api'; \
      pip freeze; } > constraints.txt

FROM scratch AS lock
COPY --from=resolucion /app/constraints.txt /

FROM base

# Capa propia para las dependencias: cambiar el código no reinstala psycopg.
# `-c` fija también las transitivas, que requirements.txt no nombra.
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

COPY pytest.ini alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY tests ./tests

# `alembic upgrade head` antes de servir. Es lo que mantiene vivo el criterio
# A1 —`docker compose up` y ya, sin pasos manuales— ahora que el esquema no lo
# crea `create_all`. Con un solo contenedor de api no hay carrera posible; si
# algún día hay varios, esto se mueve a un paso de despliegue aparte.
#
# El puerto llega por entorno, no escrito aquí (A3). Por eso `sh -c`: la forma
# exec de CMD no expande variables.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT}"]
