"""Infraestructura común de las pruebas.

Se prueba contra Postgres real, no contra SQLite: el §3 eligió Postgres por
motivos concretos —dos personas escribiendo a la vez— y sustituirlo por otro
motor en las pruebas sería probar un sistema distinto del que se despliega.

Pero contra una base **aparte**. Compartirla con la de desarrollo parecía
funcionar mientras estaba vacía y se rompió en cuanto la siembra insertó
usuarios de verdad: las pruebas veían filas de fuera de su transacción y
chocaban con la restricción de unicidad. Una suite que depende de que la base
esté vacía no está aislada, solo tiene suerte.

Dentro de esa base, cada prueba corre en una transacción externa que se
revierte. `join_transaction_mode="create_savepoint"` convierte un `commit`
del código en un savepoint, así que ni el que confirma de verdad deja rastro.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Base

_URL_DESARROLLO = make_url(settings.database_url)
_URL_PRUEBAS = _URL_DESARROLLO.set(database=f"{_URL_DESARROLLO.database}_test")


def _crear_base_si_falta() -> None:
    """`CREATE DATABASE` no admite parámetros ni corre dentro de una
    transacción: de ahí el AUTOCOMMIT y el nombre entrecomillado. El nombre
    sale de nuestra propia configuración, no de una entrada externa.
    """
    admin = create_engine(
        _URL_DESARROLLO.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with admin.connect() as conexion:
            existe = conexion.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :nombre"),
                {"nombre": _URL_PRUEBAS.database},
            ).scalar()
            if not existe:
                conexion.execute(text(f'CREATE DATABASE "{_URL_PRUEBAS.database}"'))
    finally:
        admin.dispose()


@pytest.fixture(scope="session")
def engine_de_prueba():
    _crear_base_si_falta()

    engine = create_engine(_URL_PRUEBAS)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def sesion_db(engine_de_prueba):
    conexion = engine_de_prueba.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()
