"""Infraestructura común de las pruebas.

Se prueba contra Postgres real, no contra SQLite: el §3 eligió Postgres por
motivos concretos —dos personas escribiendo a la vez— y sustituirlo por otro
motor en las pruebas sería probar un sistema distinto del que se despliega.

Cada prueba corre dentro de una transacción externa que se revierte al final.
`join_transaction_mode="create_savepoint"` hace que un `commit` dentro de la
prueba se convierta en un savepoint, así que ni el código que confirma de
verdad deja rastro en la base.
"""

import pytest
from sqlalchemy.orm import Session

from app.db import engine
from app.models import Base


@pytest.fixture(scope="session", autouse=True)
def _crear_tablas():
    Base.metadata.create_all(engine)


@pytest.fixture
def sesion_db():
    conexion = engine.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()
