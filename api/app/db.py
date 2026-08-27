"""Conexión a Postgres.

`pool_pre_ping` verifica la conexión antes de entregarla: sin eso, cada
reinicio de la base deja conexiones muertas en el pool y el primer sondeo de
salud posterior falla por una razón que no es la real.
"""

from sqlalchemy import create_engine

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
