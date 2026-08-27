"""Criterio A4 — la sonda emite la cookie con los atributos de la sesión real.

Estas pruebas no validan una funcionalidad: validan el **instrumento**. Si la
sonda emitiera atributos más permisivos que los de la sesión, la prueba por
Tailscale saldría verde y el login fallaría igual después. Un instrumento mal
calibrado es peor que no medir.
"""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.probe import COOKIE_NAME


@pytest.fixture
def cliente() -> TestClient:
    """Cliente nuevo por prueba: `TestClient` guarda cookies como un navegador,
    y compartirlo haría que el orden de las pruebas cambiara el resultado.
    """
    return TestClient(main.app)


def test_la_sonda_emite_los_atributos_de_la_sesion_real(cliente: TestClient):
    respuesta = cliente.post("/api/_probe/cookie")

    assert respuesta.status_code == 200

    cabecera = respuesta.headers["set-cookie"].lower()
    assert f"{COOKIE_NAME}=" in cabecera
    assert "httponly" in cabecera
    assert "samesite=lax" in cabecera
    assert "path=/" in cabecera

    # `COOKIE_SECURE` va en false: la variante A del ADR 0002 es HTTP plano
    # sobre Tailscale, y una cookie `Secure` sencillamente no viajaría.
    # Se compara con el separador para no confundirlo con el valor aleatorio.
    assert "; secure" not in cabecera


def test_el_navegador_devuelve_la_cookie(cliente: TestClient):
    emitida = cliente.post("/api/_probe/cookie").json()["issued"]

    leida = cliente.get("/api/_probe/cookie").json()

    assert leida["present"] is True
    assert leida["value"] == emitida


def test_sin_cookie_la_sonda_lo_dice(cliente: TestClient):
    leida = cliente.get("/api/_probe/cookie").json()

    assert leida == {"present": False, "value": None}


def test_se_puede_limpiar_para_repetir_la_prueba(cliente: TestClient):
    cliente.post("/api/_probe/cookie")
    cliente.delete("/api/_probe/cookie")

    assert cliente.get("/api/_probe/cookie").json()["present"] is False
