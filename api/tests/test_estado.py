"""Criterios K1–K4 — la pieza gana estado, y la API dice de quién es.

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
from app.models import DE_QUIEN_ES, ESTADOS, Pieza
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


def _entrar_como(cliente: TestClient, usuario: str) -> None:
    respuesta = cliente.post(
        "/api/auth/login", json={"usuario": usuario, "password": CLAVE}
    )
    assert respuesta.status_code == 200, "la prueba necesita una sesión válida"


def _pieza_en(sesion_db: Session, estado: str = "investigacion") -> Pieza:
    pieza = Pieza(titulo="Las Pléyades", creada_por="johan", estado=estado)
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
    pieza = _pieza_en(sesion_db)
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
    _entrar_como(cliente, "dathzon")
    pieza = _pieza_en(sesion_db)

    cliente.patch(f"/api/piezas/{pieza.id}", json={"estado": "publicada"})

    sesion_db.refresh(pieza)
    assert pieza.estado == "investigacion"


# --- K4 ---


@pytest.mark.parametrize(
    "estado, de_quien_es",
    [
        ("investigacion", "investigador"),
        ("solicitud_entregada", "investigador"),
        ("material_aprobado", "editor"),
        ("finalizada", "investigador"),
        ("diseno_aprobado", "investigador"),
        ("publicada", None),
    ],
)
def test_la_api_dice_de_quien_es_cada_pieza(
    cliente: TestClient, sesion_db: Session, estado: str, de_quien_es: str | None
):
    """El §2 del documento, estado por estado. `publicada` no es de nadie: el
    flujo terminó y ninguno tiene nada que hacer con ella.
    """
    pieza = _pieza_en(sesion_db, estado)
    _entrar_como(cliente, "dathzon")

    respuesta = cliente.get(f"/api/piezas/{pieza.id}").json()

    assert respuesta["estado"] == estado
    assert respuesta["de_quien_es"] == de_quien_es


def test_cada_estado_tiene_decidido_de_quien_es():
    """Añadir un estado obliga a decidir de quién es, o la API no sabría qué
    responder.
    """
    assert set(DE_QUIEN_ES) == set(ESTADOS)


@pytest.mark.parametrize(
    "estado, usuario, esperadas",
    [
        ("investigacion", "johan", {"entregar"}),
        ("investigacion", "dathzon", set()),
        ("material_aprobado", "johan", {"reformular"}),
        ("material_aprobado", "dathzon", {"finalizar", "reformular"}),
        ("finalizada", "johan", {"devolver", "aprobar_diseno", "reformular"}),
        ("finalizada", "dathzon", {"reformular"}),
        ("publicada", "johan", set()),
        ("publicada", "dathzon", set()),
    ],
)
def test_las_transiciones_dependen_de_quien_pregunta(
    cliente: TestClient,
    sesion_db: Session,
    estado: str,
    usuario: str,
    esperadas: set[str],
):
    """Son las que el `POST` aceptaría, porque salen de la misma tabla que decide
    el 403. El cliente pinta esas y no otras (N2).
    """
    pieza = _pieza_en(sesion_db, estado)
    _entrar_como(cliente, usuario)

    respuesta = cliente.get(f"/api/piezas/{pieza.id}").json()

    assert set(respuesta["transiciones"]) == esperadas


def test_la_lista_trae_las_transiciones_de_quien_pregunta(
    cliente: TestClient, sesion_db: Session
):
    _pieza_en(sesion_db)
    _entrar_como(cliente, "johan")

    [pieza] = cliente.get("/api/piezas").json()

    assert pieza["transiciones"] == ["entregar"]
