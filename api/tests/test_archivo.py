"""Criterios BD de la Fase 12 — una pieza no se borra, se archiva.

Borrarla pediría borrar su historia, que es append-only (§2.6, ADR 0008).
Archivada, sale del taller —la lista, el tablero, el aviso y el atasco— y
sigue entera en la base.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza, Traspaso
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


@pytest.fixture
def pieza(sesion_db: Session) -> Pieza:
    pieza = Pieza(titulo="Prueba de traspaso", creada_por="johan")
    sesion_db.add(pieza)
    sesion_db.commit()
    return pieza


def _entrar_como(cliente: TestClient, usuario: str = "johan") -> None:
    respuesta = cliente.post("/api/auth/login", json={"usuario": usuario, "password": CLAVE})
    assert respuesta.status_code == 200


def _ids(cliente: TestClient, ruta: str) -> list[int]:
    return [p.get("id", p.get("pieza_id")) for p in cliente.get(ruta).json()]


# --- BD1: quién ---


@pytest.mark.parametrize("accion", ["archivar", "desarchivar"])
def test_el_editor_no_archiva_ni_recupera(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, accion: str
):
    _entrar_como(cliente, "dathzon")

    assert cliente.post(f"/api/piezas/{pieza.id}/{accion}").status_code == 403
    sesion_db.refresh(pieza)
    assert pieza.archivada_en is None


@pytest.mark.parametrize("accion", ["archivar", "desarchivar"])
def test_sin_sesion_es_401(cliente: TestClient, pieza: Pieza, accion: str):
    assert cliente.post(f"/api/piezas/{pieza.id}/{accion}").status_code == 401


def test_una_pieza_que_no_existe_es_404(cliente: TestClient):
    _entrar_como(cliente)

    assert cliente.post("/api/piezas/999999/archivar").status_code == 404


# --- BD2: sale del taller ---


def test_archivada_sale_de_la_lista_y_del_atasco(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)
    assert pieza.id in _ids(cliente, "/api/piezas")
    assert pieza.id in _ids(cliente, "/api/atasco")

    respuesta = cliente.post(f"/api/piezas/{pieza.id}/archivar")

    assert respuesta.status_code == 200
    assert respuesta.json()["archivada_en"] is not None
    assert pieza.id not in _ids(cliente, "/api/piezas")
    assert pieza.id not in _ids(cliente, "/api/atasco")
    assert _ids(cliente, "/api/piezas?archivadas=true") == [pieza.id]


def test_el_editor_tampoco_la_ve_en_su_lista(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)
    cliente.post(f"/api/piezas/{pieza.id}/archivar")
    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "dathzon")

    assert pieza.id not in _ids(cliente, "/api/piezas")


def test_archivar_no_borra_nada(cliente: TestClient, pieza: Pieza, sesion_db: Session):
    """§2.6: la historia sigue ahí, y la pieza se abre por su dirección."""
    _entrar_como(cliente)
    cliente.post(f"/api/piezas/{pieza.id}/traspasos", json={"transicion": "entregar", "desde": "investigacion"})
    antes = sesion_db.query(Traspaso).filter_by(pieza_id=pieza.id).count()
    assert antes == 1

    cliente.post(f"/api/piezas/{pieza.id}/archivar")

    assert sesion_db.query(Traspaso).filter_by(pieza_id=pieza.id).count() == antes
    assert cliente.get(f"/api/piezas/{pieza.id}").json()["titulo"] == "Prueba de traspaso"


def test_archivar_dos_veces_no_mueve_la_fecha(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)

    primera = cliente.post(f"/api/piezas/{pieza.id}/archivar").json()["archivada_en"]
    segunda = cliente.post(f"/api/piezas/{pieza.id}/archivar").json()["archivada_en"]

    assert segunda == primera


# --- BD3: vuelve ---


def test_recuperada_vuelve_al_taller_como_estaba(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)
    cliente.post(f"/api/piezas/{pieza.id}/archivar")

    respuesta = cliente.post(f"/api/piezas/{pieza.id}/desarchivar")

    assert respuesta.json()["archivada_en"] is None
    assert respuesta.json()["estado"] == "investigacion"
    assert pieza.id in _ids(cliente, "/api/piezas")
    assert _ids(cliente, "/api/piezas?archivadas=true") == []
