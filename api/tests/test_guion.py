"""Criterios H1–H3 — la pieza gana guion, y el guion conserva el LaTeX.

El contenido de Voz del Cosmos lleva fórmulas y el vault tiene Latex Suite:
romperlas es corromper la pieza, no un detalle de formato. Y se rompen sin
hacer ruido — `\\nabla` empieza por `\\n` y `\\frac` por `\\f`, que en JSON son
los escapes de nueva línea y avance de página. Un tratamiento ingenuo del
texto en cualquier capa convierte una ecuación en un salto de línea y la nota
llega al vault mutilada sin que salte ningún error.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

# Deliberadamente lleno de trampas: `\n`, `\f`, llaves, subíndices y un
# símbolo fuera de ASCII.
GUION_CON_LATEX = r"""## Guion

El campo eléctrico cumple $\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}$.

La ecuación de onda:

$$
\frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 u
$$

Una masa solar es $M_\odot \approx 1.989 \times 10^{30}\,\mathrm{kg}$.
"""


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
    assert (
        cliente.post(
            "/api/auth/login", json={"usuario": usuario, "password": CLAVE}
        ).status_code
        == 200
    )


def _crear(cliente: TestClient, **campos) -> dict:
    respuesta = cliente.post(
        "/api/piezas", json={"titulo": "Ondas gravitacionales", **campos}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


# --- H1 ---


def test_la_pieza_tiene_los_campos_nuevos_y_ninguno_es_estado():
    """§2.8 sigue vigente: la máquina de estados no se inventa."""
    columnas = set(Pieza.__table__.columns.keys())

    assert columnas == {
        "id",
        "titulo",
        "creada_en",
        "creada_por",
        "guion",
        "formato",
        "tema",
        "plataforma",
        "respaldo",
    }
    assert "estado" not in columnas


def test_una_pieza_nace_sin_guion(cliente: TestClient):
    """Crear con solo el título tiene que seguir funcionando: es lo que hace
    C2 y no se rompe porque la pieza haya crecido.
    """
    _entrar_como(cliente, "johan")

    creada = _crear(cliente)

    assert creada["guion"] == ""
    assert creada["formato"] is None


def test_el_formato_se_limita_a_los_de_la_plantilla(cliente: TestClient):
    """La plantilla del vault pregunta «reel/carrusel/video/post». Aceptar
    cualquier cadena dejaría que un dedazo llegara al frontmatter.
    """
    _entrar_como(cliente, "johan")

    respuesta = cliente.post(
        "/api/piezas", json={"titulo": "x", "formato": "tiktok-vertical"}
    )

    assert respuesta.status_code == 422


# --- H2: el viaje completo del LaTeX ---


def test_el_guion_conserva_el_latex_al_guardarlo_y_leerlo(cliente: TestClient):
    _entrar_como(cliente, "johan")
    creada = _crear(cliente)

    cliente.patch(f"/api/piezas/{creada['id']}", json={"guion": GUION_CON_LATEX})
    leida = cliente.get(f"/api/piezas/{creada['id']}").json()

    assert leida["guion"] == GUION_CON_LATEX


def test_las_secuencias_peligrosas_sobreviven_intactas(cliente: TestClient):
    """Lo que de verdad se comprueba: que `\\nabla` siga siendo ocho
    caracteres y no un salto de línea seguido de `abla`.
    """
    _entrar_como(cliente, "johan")
    creada = _crear(cliente)
    cliente.patch(f"/api/piezas/{creada['id']}", json={"guion": GUION_CON_LATEX})

    guion = cliente.get(f"/api/piezas/{creada['id']}").json()["guion"]

    assert "\\nabla" in guion
    assert "\\frac" in guion
    assert "\n" + "abla" not in guion
    assert "$$" in guion
    assert r"M_\odot" in guion


def test_el_latex_llega_intacto_hasta_postgres(
    cliente: TestClient, sesion_db: Session
):
    """Sin pasar por la API al leer: se comprueba la columna directamente, por
    si la ida y la vuelta se compensaran mutuamente un error.
    """
    _entrar_como(cliente, "johan")
    creada = _crear(cliente)
    cliente.patch(f"/api/piezas/{creada['id']}", json={"guion": GUION_CON_LATEX})

    guardado = sesion_db.execute(
        sql_text("SELECT guion FROM pieza WHERE id = :id"), {"id": creada["id"]}
    ).scalar_one()

    assert guardado == GUION_CON_LATEX


# --- H3: el respaldo enlazado ---


def test_una_pieza_referencia_notas_de_respaldo(cliente: TestClient):
    _entrar_como(cliente, "johan")
    creada = _crear(cliente)

    actualizada = cliente.patch(
        f"/api/piezas/{creada['id']}",
        json={"respaldo": ["GWTC-5", "GW231123 - una fusion"]},
    ).json()

    assert actualizada["respaldo"] == ["GWTC-5", "GW231123 - una fusion"]


def test_el_respaldo_arranca_vacio(cliente: TestClient):
    _entrar_como(cliente, "johan")

    assert _crear(cliente)["respaldo"] == []


# --- Autorización de la edición ---


def test_el_editor_puede_editar_el_guion(cliente: TestClient):
    """Decisión de Johan, no deducción mía.

    Yo había restringido esto al investigador leyendo el §1, y era inventarme
    el dominio — justo lo que el §2.8 prohíbe. Los dos escriben el guion.
    """
    _entrar_como(cliente, "johan")
    creada = _crear(cliente)

    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "dathzon")

    respuesta = cliente.patch(
        f"/api/piezas/{creada['id']}", json={"guion": "corregido por el editor"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["guion"] == "corregido por el editor"


def test_el_editor_no_toca_el_respaldo_cientifico(cliente: TestClient):
    """El respaldo sigue siendo del investigador, y no por jerarquía.

    El ADR 0001 le da `literature` solo a Johan, y H4 ya devuelve 403 al
    editor en `/api/respaldo`. Dejarle escribir `respaldo` sería permitirle
    enlazar notas de una lista que no puede ver — nombres a ciegas que luego
    salen en el frontmatter de la nota exportada.
    """
    _entrar_como(cliente, "johan")
    creada = _crear(cliente)

    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "dathzon")

    respuesta = cliente.patch(
        f"/api/piezas/{creada['id']}", json={"respaldo": ["inventada"]}
    )

    assert respuesta.status_code == 403


def test_el_editor_si_puede_leer_el_guion(cliente: TestClient):
    _entrar_como(cliente, "johan")
    creada = _crear(cliente)
    cliente.patch(f"/api/piezas/{creada['id']}", json={"guion": GUION_CON_LATEX})

    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "dathzon")

    respuesta = cliente.get(f"/api/piezas/{creada['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["guion"] == GUION_CON_LATEX


def test_una_pieza_que_no_existe_da_404(cliente: TestClient):
    _entrar_como(cliente, "johan")

    assert cliente.get("/api/piezas/99999").status_code == 404
