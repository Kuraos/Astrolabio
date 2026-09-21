"""Criterios P1–P4 — los enlaces de referencia de la pieza.

Lo que Johan le pasa al editor para hacer la pieza, y que hoy va por chat. Las
pruebas le pegan directamente a la API, como las de C: qué enlace es aceptable
lo decide el servidor, no el formulario (§2.3).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Enlace, Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"
PIN = "https://www.pinterest.com/pin/1234567890/"


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


def _entrar_como(cliente: TestClient, usuario: str) -> None:
    respuesta = cliente.post(
        "/api/auth/login", json={"usuario": usuario, "password": CLAVE}
    )
    assert respuesta.status_code == 200, "la prueba necesita una sesión válida"


def _anadir(cliente: TestClient, pieza: Pieza, url: str = PIN, **extra):
    return cliente.post(
        f"/api/piezas/{pieza.id}/enlaces", json={"url": url, **extra}
    )


# --- P1 ---


def test_un_enlace_guarda_url_nota_quien_y_cuando(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente, "johan")

    respuesta = _anadir(cliente, pieza, nota="La paleta de este pin")

    assert respuesta.status_code == 201, respuesta.text
    enlace = respuesta.json()
    assert enlace["url"] == PIN
    assert enlace["nota"] == "La paleta de este pin"
    assert enlace["creado_por"] == "johan"
    assert enlace["creado_en"]


def test_quien_sale_de_la_sesion_y_no_del_cuerpo(cliente: TestClient, pieza: Pieza):
    """Como `creada_por`: si lo mandara el cliente, cualquiera podría
    atribuirle un enlace al otro.
    """
    _entrar_como(cliente, "johan")

    respuesta = _anadir(cliente, pieza, creado_por="dathzon")

    assert respuesta.json()["creado_por"] == "johan"


# --- P2 ---


@pytest.mark.parametrize("usuario", ["johan", "dathzon"])
def test_los_dos_anaden_enlaces(cliente: TestClient, pieza: Pieza, usuario: str):
    _entrar_como(cliente, usuario)

    assert _anadir(cliente, pieza).status_code == 201


def test_cualquiera_quita_el_enlace_del_otro(
    cliente: TestClient, pieza: Pieza, sesion_db: Session
):
    """Decisión 6 de la Fase 3: lo quita cualquiera, igual que lo añade."""
    _entrar_como(cliente, "johan")
    enlace = _anadir(cliente, pieza).json()
    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "dathzon")

    respuesta = cliente.delete(f"/api/piezas/{pieza.id}/enlaces/{enlace['id']}")

    assert respuesta.status_code == 204
    assert sesion_db.get(Enlace, enlace["id"]) is None


def test_no_se_quita_un_enlace_desde_la_ruta_de_otra_pieza(
    cliente: TestClient, pieza: Pieza, sesion_db: Session
):
    """El enlace tiene que ser de la pieza que dice la ruta. Si no, 404, y el
    enlace sigue donde estaba.
    """
    otra = Pieza(titulo="Otra pieza", creada_por="johan")
    sesion_db.add(otra)
    sesion_db.flush()
    _entrar_como(cliente, "johan")
    enlace = _anadir(cliente, pieza).json()

    respuesta = cliente.delete(f"/api/piezas/{otra.id}/enlaces/{enlace['id']}")

    assert respuesta.status_code == 404
    assert sesion_db.get(Enlace, enlace["id"]) is not None


# --- P3 ---


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(document.cookie)",
        "data:text/html,<script>alert(1)</script>",
        "file:///C:/Users/johan/diario.md",
        "ftp://ejemplo.com/imagen.png",
        "mailto:johan@ejemplo.com",
        "/api/piezas",
        "",
    ],
    ids=["javascript", "data", "file", "ftp", "mailto", "relativa", "vacia"],
)
def test_solo_se_aceptan_enlaces_http_o_https(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, url: str
):
    """Un `javascript:` en un enlace es un XSS esperando el clic. Y un 422 no
    deja nada escrito.
    """
    _entrar_como(cliente, "johan")

    respuesta = _anadir(cliente, pieza, url=url)

    assert respuesta.status_code == 422
    assert sesion_db.query(Enlace).count() == 0


@pytest.mark.parametrize(
    "url", ["https://youtu.be/abc123?t=30", "http://ejemplo.com/articulo"]
)
def test_http_y_https_si_entran(cliente: TestClient, pieza: Pieza, url: str):
    _entrar_como(cliente, "johan")

    respuesta = _anadir(cliente, pieza, url=url)

    assert respuesta.status_code == 201
    assert respuesta.json()["url"] == url


# --- P4 ---


def test_los_enlaces_vuelven_en_orden_de_llegada(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente, "johan")
    urls = [
        "https://ejemplo.com/uno",
        "https://ejemplo.com/dos",
        "https://ejemplo.com/tres",
    ]
    for url in urls:
        assert _anadir(cliente, pieza, url=url).status_code == 201

    respuesta = cliente.get(f"/api/piezas/{pieza.id}/enlaces")

    assert [enlace["url"] for enlace in respuesta.json()] == urls


@pytest.mark.parametrize("metodo", ["GET", "POST"])
def test_los_enlaces_de_una_pieza_que_no_existe_son_404(
    cliente: TestClient, metodo: str
):
    _entrar_como(cliente, "johan")

    respuesta = cliente.request(
        metodo, "/api/piezas/999999/enlaces", json={"url": PIN}
    )

    assert respuesta.status_code == 404
