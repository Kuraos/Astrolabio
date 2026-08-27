"""Conexión a Postgres.

`pool_pre_ping` verifica la conexión antes de entregarla: sin eso, cada
reinicio de la base deja conexiones muertas en el pool y el primer sondeo de
salud posterior falla por una razón que no es la real.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


def get_db() -> Iterator[Session]:
    """Sesión por petición. Las pruebas la sustituyen por una transacción que
    se revierte, así que el mismo código corre contra la base real sin dejar
    filas detrás.
    """
    with Session(engine) as session:
        yield session
