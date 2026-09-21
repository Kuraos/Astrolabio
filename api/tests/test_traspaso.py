"""Criterio M2 — la historia de la pieza solo crece.

De `traspaso` sale la métrica del §2.6, cuánto tarda una pieza en cada etapa, y
una historia que se puede reescribir no mide nada. Por eso estas pruebas no
comprueban que el código evite el `UPDATE`: lo ejecutan por SQL, como lo haría
un script de corrección o una sesión de `psql`, y esperan que la base lo
rechace (ADR 0008). Así fallan también si una migración retira el trigger.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.models import Pieza, Traspaso


def _un_traspaso(sesion_db: Session) -> Traspaso:
    pieza = Pieza(titulo="Las Pléyades", creada_por="johan")
    sesion_db.add(pieza)
    sesion_db.flush()

    traspaso = Traspaso(
        pieza_id=pieza.id,
        transicion="entregar",
        desde="investigacion",
        hacia="solicitud_entregada",
        creado_por="johan",
    )
    sesion_db.add(traspaso)
    sesion_db.flush()
    return traspaso


def test_la_historia_crece(sesion_db: Session):
    """Append-only es la mitad de la regla: insertar sí se puede."""
    primero = _un_traspaso(sesion_db)
    sesion_db.add(
        Traspaso(
            pieza_id=primero.pieza_id,
            transicion="devolver",
            desde="solicitud_entregada",
            hacia="investigacion",
            creado_por="dathzon",
            nota="Hay dos errores de ortografía en el copy.",
        )
    )
    sesion_db.flush()

    historia = sesion_db.query(Traspaso).filter_by(pieza_id=primero.pieza_id)
    assert historia.count() == 2


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE traspaso SET nota = 'reescrita' WHERE id = {id}",
        "DELETE FROM traspaso WHERE id = {id}",
        "TRUNCATE traspaso",
    ],
    ids=["update", "delete", "truncate"],
)
def test_la_base_no_deja_reescribir_la_historia(sesion_db: Session, sentencia: str):
    """`TRUNCATE` también: es un borrado sin `WHERE`, y un trigger por fila no
    lo vería.
    """
    traspaso = _un_traspaso(sesion_db)

    with pytest.raises(DBAPIError, match="append-only"):
        sesion_db.execute(text(sentencia.format(id=traspaso.id)))
