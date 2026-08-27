FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Capa propia para las dependencias: cambiar el código no reinstala psycopg.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

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
