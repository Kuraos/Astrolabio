"""Criterios AD1–AD3 de la Fase 6 — las tareas.

Las de cada pieza, su checklist, y las sueltas, que no son de ninguna. Los dos
roles hacen todo con cualquiera, como con el material (§7.5), así que no hay
ningún 403 que probar: lo que se prueba es que cada acción funciona con cada
rol, y que quién crea y quién marca sale de la sesión.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"
USUARIOS = ["johan", "dathzon"]


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


def _crear(cliente: TestClient, **cuerpo) -> dict:
    respuesta = cliente.post("/api/tareas", json=cuerpo)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _marcar(cliente: TestClient, tarea: dict, **cuerpo):
    return cliente.patch(f"/api/tareas/{tarea['id']}", json=cuerpo)


# --- AD1 y AD3: crearlas, con pieza o sueltas ---


@pytest.mark.parametrize("usuario", USUARIOS)
def test_los_dos_roles_crean_una_tarea_de_la_pieza(
    cliente: TestClient, pieza: Pieza, usuario: str
):
    _entrar_como(cliente, usuario)

    tarea = _crear(cliente, texto="Buscar la imagen del Hubble", pieza_id=pieza.id)

    assert tarea["texto"] == "Buscar la imagen del Hubble"
    assert tarea["pieza_id"] == pieza.id
    assert tarea["hecha"] is False
    assert tarea["marcada_por"] is None
    assert tarea["creada_por"] == usuario


@pytest.mark.parametrize("usuario", USUARIOS)
def test_los_dos_roles_crean_una_tarea_suelta(cliente: TestClient, usuario: str):
    """§7.1: sin pieza, como «comprar el micrófono»."""
    _entrar_como(cliente, usuario)

    tarea = _crear(cliente, texto="Comprar el micrófono")

    assert tarea["pieza_id"] is None
    assert tarea["creada_por"] == usuario


def test_quien_la_crea_sale_de_la_sesion(cliente: TestClient):
    """Como `creada_por` en la pieza (M1): si lo mandara el cliente, cualquiera
    podría atribuirle una tarea al otro.
    """
    _entrar_como(cliente, "dathzon")

    tarea = _crear(cliente, texto="Comprar el micrófono", creada_por="johan")

    assert tarea["creada_por"] == "dathzon"


@pytest.mark.parametrize("texto", ["", "   "])
def test_un_texto_vacio_es_422(cliente: TestClient, texto: str):
    _entrar_como(cliente)

    assert cliente.post("/api/tareas", json={"texto": texto}).status_code == 422


def test_el_texto_se_guarda_sin_espacios_alrededor(cliente: TestClient):
    _entrar_como(cliente)

    assert _crear(cliente, texto="  Grabar la voz  ")["texto"] == "Grabar la voz"


def test_una_pieza_que_no_existe_es_404(cliente: TestClient):
    _entrar_como(cliente)

    respuesta = cliente.post("/api/tareas", json={"texto": "Algo", "pieza_id": 999999})

    assert respuesta.status_code == 404


# --- AD1 y AD3: marcarlas y desmarcarlas ---


@pytest.mark.parametrize("usuario", USUARIOS)
def test_los_dos_roles_marcan_y_queda_quien_y_cuando(
    cliente: TestClient, pieza: Pieza, usuario: str
):
    _entrar_como(cliente, usuario)
    tarea = _crear(cliente, texto="Grabar la voz", pieza_id=pieza.id)

    respuesta = _marcar(cliente, tarea, hecha=True)

    assert respuesta.status_code == 200
    assert respuesta.json()["hecha"] is True
    assert respuesta.json()["marcada_por"] == usuario
    assert respuesta.json()["marcada_en"] is not None


@pytest.mark.parametrize("usuario", USUARIOS)
def test_los_dos_roles_desmarcan_y_se_borra_quien_la_marco(
    cliente: TestClient, pieza: Pieza, usuario: str
):
    """AD1: desmarcada, nadie la marcó. Dejar el nombre diría lo contrario."""
    _entrar_como(cliente, usuario)
    tarea = _crear(cliente, texto="Grabar la voz", pieza_id=pieza.id)
    _marcar(cliente, tarea, hecha=True)

    respuesta = _marcar(cliente, tarea, hecha=False)

    assert respuesta.status_code == 200
    assert respuesta.json()["hecha"] is False
    assert respuesta.json()["marcada_por"] is None
    assert respuesta.json()["marcada_en"] is None


def test_quien_la_marca_sale_de_la_sesion(cliente: TestClient):
    _entrar_como(cliente, "dathzon")
    tarea = _crear(cliente, texto="Grabar la voz")

    respuesta = _marcar(cliente, tarea, hecha=True, marcada_por="johan")

    assert respuesta.json()["marcada_por"] == "dathzon"


def test_marcarla_otra_vez_no_cambia_quien_la_marco(cliente: TestClient):
    """Si los dos la marcan a la vez, la marcó el primero: la segunda marca no
    le quita el crédito.
    """
    _entrar_como(cliente, "johan")
    tarea = _crear(cliente, texto="Grabar la voz")
    marcada = _marcar(cliente, tarea, hecha=True).json()

    _entrar_como(cliente, "dathzon")
    otra_vez = _marcar(cliente, tarea, hecha=True).json()

    assert otra_vez["marcada_por"] == "johan"
    assert otra_vez["marcada_en"] == marcada["marcada_en"]


def test_marcar_una_tarea_que_no_existe_es_404(cliente: TestClient):
    _entrar_como(cliente)

    assert cliente.patch("/api/tareas/999999", json={"hecha": True}).status_code == 404


# --- AD2 y AD3: todas en un pedido, y quitarlas ---


@pytest.mark.parametrize("usuario", USUARIOS)
def test_los_dos_roles_ven_todas_en_orden_de_llegada(
    cliente: TestClient, pieza: Pieza, usuario: str
):
    """AD2: las de las piezas y las sueltas juntas, porque el tablero cuenta las
    de cada pieza y la pantalla principal enseña las sueltas.
    """
    _entrar_como(cliente, "johan")
    primera = _crear(cliente, texto="Grabar la voz", pieza_id=pieza.id)
    segunda = _crear(cliente, texto="Comprar el micrófono")
    _entrar_como(cliente, usuario)

    respuesta = cliente.get("/api/tareas")

    assert respuesta.status_code == 200
    assert [t["id"] for t in respuesta.json()] == [primera["id"], segunda["id"]]


@pytest.mark.parametrize("usuario", USUARIOS)
def test_los_dos_roles_quitan_una_tarea(cliente: TestClient, usuario: str):
    """No es historia (§2.6), como el material: quitarla la borra."""
    _entrar_como(cliente, "johan")
    tarea = _crear(cliente, texto="Comprar el micrófono")
    _entrar_como(cliente, usuario)

    respuesta = cliente.delete(f"/api/tareas/{tarea['id']}")

    assert respuesta.status_code == 204
    assert cliente.get("/api/tareas").json() == []


def test_quitar_una_tarea_que_no_existe_es_404(cliente: TestClient):
    _entrar_como(cliente)

    assert cliente.delete("/api/tareas/999999").status_code == 404
