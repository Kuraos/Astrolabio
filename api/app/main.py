"""API de Astrolabio.

Fase 0: sin dominio. La única ruta que existe es la de salud, y existe para
demostrar que el camino navegador → proxy → api → Postgres está completo.
Los estados del flujo no se modelan hasta la conversación con el editor
(CLAUDE.md §2.8).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .auth import router as auth_router
from .db import engine
from .models import Base
from .piezas import router as piezas_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    # `create_all` basta en la Fase 0 y el alcance lo dice explícitamente.
    # En cuanto haya un modelo de dominio real, Alembic (CLAUDE.md §4).
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Astrolabio API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(piezas_router)


def _sondear_base() -> tuple[bool, str | None]:
    """Ejecuta una consulta real contra Postgres.

    Devuelve solo el *nombre* de la excepción, nunca su texto: los errores de
    SQLAlchemy arrastran la cadena de conexión, y ahí va la contraseña de la
    base. Un endpoint de salud es público por definición.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return False, type(exc).__name__
    return True, None


@app.get("/api/health")
def health(response: Response) -> dict:
    """Criterio A2: el estado de la conexión real, no un `{"ok": true}` fijo.

    Si Postgres no responde, el código es 503. Un health que devuelve 200 con
    la base caída no sirve ni para el `depends_on` de compose ni para
    diagnosticar a distancia, que son sus dos únicos usos.
    """
    conectada, error = _sondear_base()

    if not conectada:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if conectada else "degraded",
        "database": {"connected": conectada, "error": error},
    }
