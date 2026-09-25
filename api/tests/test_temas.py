"""Criterios Y1–Y4 de la Fase 5 — el tema cerrado y las etiquetas de la pieza.

Como las de C, le pegan directamente a la API: qué tema vale y cómo queda una
etiqueta lo decide el servidor, no el formulario (§2.3).
"""

import unicodedata

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza
from app.piezas import normalizar_etiqueta
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"
TEMAS = ["Sistema Solar", "Estrellas", "Galaxias y cosmología", "Exploración espacial"]


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


# --- Y1: el tema, de una lista cerrada ---


@pytest.mark.parametrize("tema", TEMAS)
def test_los_cuatro_temas_se_aceptan(cliente: TestClient, pieza: Pieza, tema: str):
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, tema=tema)

    assert respuesta.status_code == 200
    assert respuesta.json()["tema"] == tema


@pytest.mark.parametrize("tema", ["Astrofísica", "estrellas", "Cúmulos abiertos", ""])
def test_un_tema_fuera_de_la_lista_es_422(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, tema: str
):
    """El ADR 0004 pide pocos temas y fijos: uno nuevo por un dedazo partiría
    las celdas de las métricas. Y un 422 no escribe nada.
    """
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, tema=tema)

    assert respuesta.status_code == 422
    sesion_db.refresh(pieza)
    assert pieza.tema is None


def test_crear_con_un_tema_fuera_de_la_lista_es_422(cliente: TestClient):
    _entrar_como(cliente)

    respuesta = cliente.post("/api/piezas", json={"titulo": "M45", "tema": "Astrofísica"})

    assert respuesta.status_code == 422


def test_una_pieza_puede_quedarse_sin_tema(cliente: TestClient, pieza: Pieza):
    """Al crearla rara vez se sabe el tema: sin él sigue siendo válida."""
    _entrar_como(cliente)
    _editar(cliente, pieza, tema="Estrellas")

    respuesta = _editar(cliente, pieza, tema=None)

    assert respuesta.status_code == 200
    assert respuesta.json()["tema"] is None


# --- Y2: las etiquetas, una lista en la pieza ---


def test_una_pieza_nueva_no_tiene_etiquetas(cliente: TestClient):
    _entrar_como(cliente)

    respuesta = cliente.post("/api/piezas", json={"titulo": "Las Pléyades"})

    assert respuesta.json()["etiquetas"] == []


def test_las_etiquetas_se_guardan(cliente: TestClient, pieza: Pieza, sesion_db: Session):
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, etiquetas=["cumulos", "m45"])

    assert respuesta.json()["etiquetas"] == ["cumulos", "m45"]
    sesion_db.refresh(pieza)
    assert pieza.etiquetas == ["cumulos", "m45"]


def test_las_etiquetas_no_se_pueden_anular(cliente: TestClient, pieza: Pieza):
    """Sin etiquetas es una lista vacía. Un `null` explícito es 422, no un 500
    de la base, que no admite nulos en la columna.
    """
    _entrar_como(cliente)

    assert _editar(cliente, pieza, etiquetas=None).status_code == 422


# --- Y3: normalizadas en el servidor ---


@pytest.mark.parametrize(
    ("escrita", "guardada"),
    [
        ("Agujeros Negros", "agujeros-negros"),
        ("  vía   láctea ", "via-lactea"),
        ("Año Luz", "año-luz"),
        ("pingüino", "pinguino"),
        ("Estrellas/Enanas blancas", "estrellas-enanas-blancas"),
        ("¿Qué es M31?", "que-es-m31"),
        ("-- a -- b --", "a-b"),
        ("gaia_dr3", "gaia_dr3"),
        # La ñ escrita como n más tilde combinante, como la dejan algunos
        # teclados: sin componerla antes, se perdería la tilde y quedaría «ano».
        (unicodedata.normalize("NFD", "año"), "año"),
    ],
)
def test_la_etiqueta_se_normaliza(escrita: str, guardada: str):
    assert normalizar_etiqueta(escrita) == guardada


@pytest.mark.parametrize("escrita", ["2026", "???", "   ", "--"])
def test_una_etiqueta_vacia_o_solo_de_numeros_no_vale(escrita: str):
    """Obsidian no reconocería ninguna de las dos como tag."""
    with pytest.raises(ValueError):
        normalizar_etiqueta(escrita)


def test_la_api_devuelve_las_etiquetas_normalizadas(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, etiquetas=["Vía Láctea"])

    assert respuesta.json()["etiquetas"] == ["via-lactea"]


def test_las_repetidas_se_quedan_en_una(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, etiquetas=["Galaxias", "galaxias", "GALAXIAS ", "m31"])

    assert respuesta.json()["etiquetas"] == ["galaxias", "m31"]


def test_una_etiqueta_que_no_vale_es_422_y_no_guarda_nada(
    cliente: TestClient, pieza: Pieza, sesion_db: Session
):
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, etiquetas=["galaxias", "2026"])

    assert respuesta.status_code == 422
    sesion_db.refresh(pieza)
    assert pieza.etiquetas == []


# --- Y4: los dos roles ---


@pytest.mark.parametrize("usuario", ["johan", "dathzon"])
def test_los_dos_cambian_tema_y_etiquetas(cliente: TestClient, pieza: Pieza, usuario: str):
    _entrar_como(cliente, usuario)

    respuesta = _editar(cliente, pieza, tema="Estrellas", etiquetas=["m45"])

    assert respuesta.status_code == 200
    assert respuesta.json()["tema"] == "Estrellas"
    assert respuesta.json()["etiquetas"] == ["m45"]
