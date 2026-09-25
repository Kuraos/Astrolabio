"""Criterios AC1 y AC2 de la Fase 6 — las fechas de la pieza.

La entrega del diseño y la publicación prevista. Como las de Y, le pegan
directamente a la API: qué es una fecha lo decide el servidor, no el campo del
navegador (§2.3).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Date
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"
FECHAS = ["fecha_entrega", "fecha_publicacion_prevista"]


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


@pytest.fixture
def pieza(sesion_db: Session) -> Pieza:
    p = Pieza(titulo="Las Pléyades", creada_por="johan")
    sesion_db.add(p)
    sesion_db.flush()
    return p


def _entrar_como(cliente: TestClient, usuario: str = "johan") -> None:
    respuesta = cliente.post(
        "/api/auth/login", json={"usuario": usuario, "password": CLAVE}
    )
    assert respuesta.status_code == 200, "la prueba necesita una sesión válida"


def _editar(cliente: TestClient, pieza: Pieza, **cambios):
    return cliente.patch(f"/api/piezas/{pieza.id}", json=cambios)


# --- AC1: días del calendario, nulos mientras no se decidan ---


@pytest.mark.parametrize("campo", FECHAS)
def test_la_columna_es_un_dia_sin_hora(campo: str):
    """`DATE` y no `timestamptz`: un día no se corre al pasar de UTC a Bogotá,
    que es lo que le pasaba a `fecha` en el exportador con `creada_en`.
    """
    assert isinstance(Pieza.__table__.columns[campo].type, Date)


def test_una_pieza_nace_sin_fechas(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)

    datos = cliente.get(f"/api/piezas/{pieza.id}").json()

    assert datos["fecha_entrega"] is None
    assert datos["fecha_publicacion_prevista"] is None


# --- AC2: los dos roles las cambian por PATCH ---


@pytest.mark.parametrize("campo", FECHAS)
@pytest.mark.parametrize("usuario", ["johan", "dathzon"])
def test_los_dos_roles_ponen_la_fecha(
    cliente: TestClient, pieza: Pieza, usuario: str, campo: str
):
    """§7.5: como el resto de la pieza. Ninguna regla nueva de quién puede qué."""
    _entrar_como(cliente, usuario)

    respuesta = _editar(cliente, pieza, **{campo: "2026-10-02"})

    assert respuesta.status_code == 200
    assert respuesta.json()[campo] == "2026-10-02"


@pytest.mark.parametrize("campo", FECHAS)
def test_null_borra_la_fecha(cliente: TestClient, pieza: Pieza, campo: str):
    _entrar_como(cliente)
    _editar(cliente, pieza, **{campo: "2026-10-02"})

    respuesta = _editar(cliente, pieza, **{campo: None})

    assert respuesta.status_code == 200
    assert respuesta.json()[campo] is None


@pytest.mark.parametrize("campo", FECHAS)
def test_no_mencionarla_no_la_borra(cliente: TestClient, pieza: Pieza, campo: str):
    """Es un `PATCH`: que `null` borre no puede hacer que omitirla también."""
    _entrar_como(cliente)
    _editar(cliente, pieza, **{campo: "2026-10-02"})

    respuesta = _editar(cliente, pieza, titulo="Las Pléyades, revisado")

    assert respuesta.json()[campo] == "2026-10-02"


@pytest.mark.parametrize("campo", FECHAS)
@pytest.mark.parametrize(
    "valor", ["mañana", "2026-02-30", "02/10/2026", "2026-10-02T15:00:00"]
)
def test_lo_que_no_es_una_fecha_es_422(
    cliente: TestClient, pieza: Pieza, campo: str, valor: str
):
    """Un día que no existe, otro formato, o una hora que diría otra cosa."""
    _entrar_como(cliente)

    assert _editar(cliente, pieza, **{campo: valor}).status_code == 422
