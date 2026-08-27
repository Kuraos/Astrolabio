"""Criterio A2 — el sondeo de salud refleja la conexión real a Postgres.

El caso feliz necesita la base arriba, que es como corre en compose:
`docker compose run api pytest` levanta `db` por el `depends_on`.
"""

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app import main

cliente = TestClient(main.app)


class _EngineCaido:
    """Sustituye al engine para simular Postgres inalcanzable.

    Se reemplaza el objeto entero en vez de parchear su método porque el
    `Engine` de SQLAlchemy no garantiza ser modificable por instancia.
    """

    def __init__(self, mensaje: str = "conexion rechazada") -> None:
        self._mensaje = mensaje

    def connect(self):
        raise OperationalError("SELECT 1", {}, Exception(self._mensaje))


def test_health_reporta_la_conexion_real():
    respuesta = cliente.get("/api/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "status": "ok",
        "database": {"connected": True, "error": None},
    }


def test_health_degrada_cuando_la_base_no_responde(monkeypatch):
    """Lo que separa A2 de un `{"ok": true}` fijo: si la base cae, se nota."""
    monkeypatch.setattr(main, "engine", _EngineCaido())

    respuesta = cliente.get("/api/health")

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "degraded"
    assert cuerpo["database"]["connected"] is False
    assert cuerpo["database"]["error"] == "OperationalError"


def test_health_no_filtra_la_cadena_de_conexion(monkeypatch):
    """La contraseña de Postgres viaja dentro de `DATABASE_URL`, y los errores
    de SQLAlchemy la arrastran en su texto. No puede salir por HTTP.
    """
    monkeypatch.setattr(
        main, "engine", _EngineCaido("password=astrolabio-dev host=db port=5432")
    )

    cuerpo = cliente.get("/api/health").text

    assert "password" not in cuerpo
    assert "astrolabio-dev" not in cuerpo
