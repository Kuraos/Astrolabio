"""Criterios B2, B3, B4 y B5 — login, logout y sesión.

Es la parte del código donde un fallo no se ve mirando la pantalla: una API
que filtra qué cuentas existen se comporta igual que una correcta hasta que
alguien la enumera.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import auth, main
from app.db import get_db
from app.models import Sesion
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"


@pytest.fixture
def cliente(sesion_db: Session):
    sembrar_usuarios(
        sesion_db,
        [Semilla(usuario="johan", password=CLAVE, rol="investigador")],
    )

    main.app.dependency_overrides[get_db] = lambda: sesion_db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def _entrar(cliente: TestClient, usuario: str = "johan", password: str = CLAVE):
    return cliente.post(
        "/api/auth/login", json={"usuario": usuario, "password": password}
    )


# --- B2 ---


def test_login_valido_emite_la_cookie_de_sesion(cliente: TestClient):
    respuesta = _entrar(cliente)

    assert respuesta.status_code == 200

    cookie = respuesta.headers["set-cookie"].lower()
    assert "astrolabio_sesion=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    # COOKIE_SECURE en false: HTTP plano sobre Tailscale (ADR 0002). Se compara
    # con el separador para no chocar con el valor aleatorio de la cookie.
    assert "; secure" not in cookie


def test_login_valido_deja_la_sesion_en_la_base(
    cliente: TestClient, sesion_db: Session
):
    """El ADR 0006 exige estado real: sin fila no hay nada que invalidar."""
    _entrar(cliente)

    assert sesion_db.query(Sesion).count() == 1


# --- B3 ---


def test_usuario_inexistente_y_clave_incorrecta_son_indistinguibles(
    cliente: TestClient,
):
    """Si las dos respuestas difieren en algo —código, cuerpo, cabecera— la
    API se convierte en un oráculo de qué cuentas existen.
    """
    inexistente = _entrar(cliente, usuario="no-existe", password="lo-que-sea")
    incorrecta = _entrar(cliente, usuario="johan", password="equivocada")

    assert inexistente.status_code == 401
    assert incorrecta.status_code == 401
    assert inexistente.json() == incorrecta.json()


def test_un_usuario_inexistente_tambien_verifica_un_hash(
    cliente: TestClient, monkeypatch: pytest.MonkeyPatch
):
    """B3 pide el mismo **coste temporal**, no solo el mismo mensaje.

    Medir el reloj es inestable y daría una prueba intermitente, así que se
    comprueba el mecanismo que produce ese coste: que la verificación de
    Argon2 se ejecute también cuando el usuario no existe. Sin eso, el caso
    inexistente responde en microsegundos y el existente en decenas de
    milisegundos, y la diferencia es medible desde fuera.
    """
    llamadas: list[tuple] = []

    def espia(*args):
        llamadas.append(args)
        return False

    monkeypatch.setattr(auth, "verify_password", espia)

    _entrar(cliente, usuario="no-existe", password="lo-que-sea")

    assert len(llamadas) == 1


# --- B5 ---


def test_me_sin_sesion_responde_401(cliente: TestClient):
    assert cliente.get("/api/auth/me").status_code == 401


def test_me_con_sesion_devuelve_usuario_y_rol(cliente: TestClient):
    _entrar(cliente)

    respuesta = cliente.get("/api/auth/me")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"usuario": "johan", "rol": "investigador"}


def test_logout_invalida_la_sesion(cliente: TestClient):
    _entrar(cliente)

    assert cliente.post("/api/auth/logout").status_code == 200
    assert cliente.get("/api/auth/me").status_code == 401


def test_logout_borra_la_fila_no_solo_la_cookie(
    cliente: TestClient, sesion_db: Session
):
    """Si solo se borrara la cookie, quien tuviera copia del testigo seguiría
    dentro. Eso es exactamente lo que el ADR 0006 descarta.
    """
    _entrar(cliente)
    cliente.post("/api/auth/logout")

    assert sesion_db.query(Sesion).count() == 0


def test_una_cookie_inventada_no_abre_sesion(cliente: TestClient):
    cliente.cookies.set("astrolabio_sesion", "testigo-que-nunca-existio")

    assert cliente.get("/api/auth/me").status_code == 401


# --- B4 ---


def test_ninguna_respuesta_de_auth_incluye_el_hash(cliente: TestClient):
    """«Ningún hash aparece en ninguna respuesta de la API, nunca»."""
    login = _entrar(cliente)
    me = cliente.get("/api/auth/me")

    for respuesta in (login, me):
        assert "argon2" not in respuesta.text
        assert "hash" not in respuesta.text.lower()
