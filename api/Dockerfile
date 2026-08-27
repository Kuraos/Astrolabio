FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Capa propia para las dependencias: cambiar el código no reinstala psycopg.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pytest.ini ./
COPY app ./app
COPY tests ./tests

# El puerto llega por entorno, no escrito aquí (A3). Por eso `sh -c`: la forma
# exec de CMD no expande variables.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT}"]
