"""Criterios C1–C5 — autorización, el corazón de la fase.

El §2.3 lo dice sin rodeos: ocultar un botón en el frontend no es
autorización, es decoración. Por eso estas pruebas le pegan **directamente a
la API** con la cookie del editor, sin pasar por el cliente: es el único
sitio donde la comprobación cuenta.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

SEMILLAS = [
    Semilla(usuario="johan", password=CLAVE, rol="investigador"),
    Semilla(usuario="dathzon", password=CLAVE, rol="editor"),
]


@pytest.fixture
def cliente(sesion_db: Session):
    sembrar_usuarios(sesion_db, SEMILLAS)

    main.app.dependency_overrides[get_db] = lambda: sesion_db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def _entrar_como(cliente: TestClient, usuario: str) -> None:
    respuesta = cliente.post(
        "/api/auth/login", json={"usuario": usuario, "password": CLAVE}
    )
    assert respuesta.status_code == 200, "la prueba necesita una sesión válida"


# --- C1 ---


def test_la_pieza_no_tiene_campo_estado():
    """§2.8: la máquina de estados sale de una conversación con el editor que
    todavía no ha ocurrido. Modelarla ahora sería inventarla, y esta prueba
    existe para que no se cuele por descuido en un refactor.

    Se afirma el invariante —los cuatro campos de C1 están, `estado` no—, no
    el conjunto exacto de columnas: la pieza puede crecer legítimamente, y de
    hecho creció en H1. Una prueba que se rompe cuando el código hace lo
    correcto acaba siendo la que alguien edita sin leer.
    La forma completa de la tabla se afirma una sola vez, en `test_guion.py`.
    """
    columnas = set(Pieza.__table__.columns.keys())

    assert {"id", "titulo", "creada_en", "creada_por"} <= columnas
    assert "estado" not in columnas


# --- C2 y C4 ---


def test_el_editor_no_puede_crear_piezas(cliente: TestClient):
    """C4: la petición va directa a la API con la cookie del editor.

    Y el código importa: 403 significa «sé quién eres y no puedes». Un 401
    diría que no se sabe quién es, un 404 escondería que la ruta existe, y un
    200 silencioso sería el peor de todos.
    """
    _entrar_como(cliente, "dathzon")

    respuesta = cliente.post("/api/piezas", json={"titulo": "Las Pléyades"})

    assert respuesta.status_code == 403


def test_el_editor_no_crea_la_pieza_ni_a_medias(
    cliente: TestClient, sesion_db: Session
):
    """Un 403 que igual escribe la fila no es autorización, es un mensaje."""
    _entrar_como(cliente, "dathzon")
    cliente.post("/api/piezas", json={"titulo": "Las Pléyades"})

    assert sesion_db.query(Pieza).count() == 0


def test_el_investigador_si_puede_crear_piezas(cliente: TestClient):
    _entrar_como(cliente, "johan")

    respuesta = cliente.post("/api/piezas", json={"titulo": "Las Pléyades"})

    assert respuesta.status_code == 201
    assert respuesta.json()["titulo"] == "Las Pléyades"


def test_la_pieza_registra_quien_la_creo(cliente: TestClient):
    """`creada_por` sale de la sesión, nunca del cuerpo de la petición: si lo
    enviara el cliente, cualquiera podría atribuirle una pieza al otro.
    """
    _entrar_como(cliente, "johan")

    creada = cliente.post("/api/piezas", json={"titulo": "Las Pléyades"}).json()

    assert creada["creada_por"] == "johan"


# --- C3 ---


def test_ambos_roles_pueden_listar_piezas(cliente: TestClient):
    _entrar_como(cliente, "johan")
    cliente.post("/api/piezas", json={"titulo": "Las Pléyades"})

    como_investigador = cliente.get("/api/piezas")

    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "dathzon")
    como_editor = cliente.get("/api/piezas")

    assert como_investigador.status_code == 200
    assert como_editor.status_code == 200
    assert como_editor.json() == como_investigador.json()


# --- C5 ---


@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("GET", "/api/piezas"),
        ("POST", "/api/piezas"),
        ("GET", "/api/auth/me"),
    ],
)
def test_sin_cookie_todo_responde_401(cliente: TestClient, metodo: str, ruta: str):
    respuesta = cliente.request(metodo, ruta, json={"titulo": "da igual"})

    assert respuesta.status_code == 401


def test_solo_health_y_login_viven_sin_sesion(cliente: TestClient):
    """C5 dice «401 en todo salvo health y login».

    Se recorre el esquema OpenAPI en vez de una lista escrita a mano: así un
    endpoint nuevo sin autenticar rompe esta prueba en lugar de pasar
    desapercibido. Y se lee del esquema, no de `app.routes`, porque FastAPI
    anida los routers incluidos y recorrer las rutas a mano solo encontraba
    las declaradas directamente sobre la aplicación — una comprobación que
    parecía funcionar mientras no hubiera nada que encontrar.
    """
    exentas = {("GET", "/api/health"), ("POST", "/api/auth/login")}

    sin_sesion = set()
    for ruta, operaciones in main.app.openapi()["paths"].items():
        for metodo in operaciones:
            if metodo.upper() not in {"GET", "POST", "DELETE", "PUT", "PATCH"}:
                continue
            respuesta = cliente.request(metodo.upper(), ruta, json={"titulo": "x"})
            if respuesta.status_code != 401:
                sin_sesion.add((metodo.upper(), ruta))

    assert sin_sesion == exentas
