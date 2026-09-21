"""Criterios K1–K3 — la pieza gana estado.

Hasta la Fase 2, `test_piezas.py` tenía una prueba que afirmaba que `pieza` no
tenía `estado`: el §2.8 prohibía inventarlo antes de hablar con el editor. La
conversación ocurrió y está escrita en `docs/estados-del-flujo.md`, y la prueba
de K2 ocupa su sitio: es la forma que tiene el §2.8 de seguir vigente.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import ESTADOS, Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"


@pytest.fixture
def cliente(sesion_db: Session):
    sembrar_usuarios(
        sesion_db,
        [
            Semilla(usuario="johan", password=CLAVE, rol="investigador"),
            Semilla(usuario="dathzon", password=CLAVE, rol="editor"),
        ],
    )
    main.app.dependency_overrides[get_db] = lambda: sesion_db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def _una_pieza(sesion_db: Session) -> Pieza:
    pieza = Pieza(titulo="Las Pléyades", creada_por="johan")
    sesion_db.add(pieza)
    sesion_db.flush()
    return pieza


# --- K1 ---


def test_toda_pieza_nace_en_investigacion(sesion_db: Session):
    """La etapa de Johan, con el nombre que le puso él.

    Se inserta por SQL sin nombrar la columna, para que conteste la base y no
    el valor por defecto del ORM: es el mismo mecanismo que les dio
    `investigacion` a las piezas que ya existían cuando llegó la columna.
    """
    estado = sesion_db.execute(
        text(
            "INSERT INTO pieza (titulo, creada_por) "
            "VALUES (:titulo, :creada_por) RETURNING estado"
        ),
        {"titulo": "Las Pléyades", "creada_por": "johan"},
    ).scalar_one()

    assert estado == "investigacion"


# --- K2 ---


def test_los_estados_son_los_del_documento():
    """Si falla porque añadiste un estado, la pregunta no es cómo arreglar la
    prueba, sino si ese estado está en `docs/estados-del-flujo.md`.
    """
    assert ESTADOS == (
        "investigacion",
        "solicitud_entregada",
        "material_aprobado",
        "finalizada",
        "diseno_aprobado",
        "publicada",
    )


def test_la_base_admite_esos_estados_y_ninguno_mas(sesion_db: Session):
    """La restricción la crea la migración con su propia copia de la lista, así
    que esta prueba vigila dos cosas: que siga ahí —la comparación de F2 no mira
    restricciones CHECK— y que su lista no se separe de la del modelo.
    """
    pieza = _una_pieza(sesion_db)
    cambiar = text("UPDATE pieza SET estado = :estado WHERE id = :id")

    for estado in ESTADOS:
        sesion_db.execute(cambiar, {"estado": estado, "id": pieza.id})

    with pytest.raises(IntegrityError):
        sesion_db.execute(cambiar, {"estado": "en_revision", "id": pieza.id})


# --- K3 ---


def test_un_patch_no_mueve_el_estado(cliente: TestClient, sesion_db: Session):
    """Solo un traspaso mueve la pieza. Si `estado` se colara en
    `PiezaEditada`, el editor podría saltar a `publicada` con un `PATCH` y
    ninguna regla de quién mueve qué valdría nada.
    """
    respuesta = cliente.post(
        "/api/auth/login", json={"usuario": "dathzon", "password": CLAVE}
    )
    assert respuesta.status_code == 200, "la prueba necesita una sesión válida"
    pieza = _una_pieza(sesion_db)

    cliente.patch(f"/api/piezas/{pieza.id}", json={"estado": "publicada"})

    sesion_db.refresh(pieza)
    assert pieza.estado == "investigacion"
