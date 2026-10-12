"""Criterios BB de la Fase 12 — una fuente nueva, creada desde Astrolabio.

La única escritura de respaldo que hace la app (ADR 0019): crea la nota y no
la vuelve a tocar. El vault es uno de mentira en `tmp_path`, como en
`test_respaldo.py`.
"""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main, respaldo
from app.db import get_db
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

FUENTE = {
    "fuente_titulo": "GW231123: a Binary Black Hole Merger with Total Mass 190-265 M☉",
    "nombre": "GW231123 - una fusión en el mass gap",
    "fuente_tipo": "paper",
    "autor": "Colaboración LIGO-Virgo-KAGRA",
    "url": "https://arxiv.org/abs/2507.08219",
    "resumen": "La fusión más masiva observada: $M \\approx 225\\,M_\\odot$.",
    "confianza": "preliminar",
}


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    (tmp_path / "Investigacion" / "Recursos").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def cliente(sesion_db: Session, vault: Path, monkeypatch: pytest.MonkeyPatch):
    sembrar_usuarios(
        sesion_db,
        [
            Semilla(usuario="johan", password=CLAVE, rol="investigador"),
            Semilla(usuario="dathzon", password=CLAVE, rol="editor"),
        ],
    )
    monkeypatch.setattr(respaldo, "carpeta_configurada", lambda: vault)

    main.app.dependency_overrides[get_db] = lambda: sesion_db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def _entrar_como(cliente: TestClient, usuario: str = "johan") -> None:
    respuesta = cliente.post("/api/auth/login", json={"usuario": usuario, "password": CLAVE})
    assert respuesta.status_code == 200


def _notas(vault: Path) -> list[Path]:
    return sorted((vault / "Investigacion" / "Recursos").iterdir())


# --- BB1: quién ---


def test_el_editor_no_crea_fuentes(cliente: TestClient, vault: Path):
    """403, y nada escrito: el respaldo es de Johan (H4, §2.3)."""
    _entrar_como(cliente, "dathzon")

    assert cliente.post("/api/fuentes", json=FUENTE).status_code == 403
    assert _notas(vault) == []


def test_sin_sesion_es_401(cliente: TestClient, vault: Path):
    assert cliente.post("/api/fuentes", json=FUENTE).status_code == 401
    assert _notas(vault) == []


# --- BB2: la nota ---


def test_la_nota_nace_como_la_pide_el_vault(cliente: TestClient, vault: Path):
    _entrar_como(cliente)

    respuesta = cliente.post("/api/fuentes", json=FUENTE)

    assert respuesta.status_code == 201
    assert respuesta.json()["archivo"] == "GW231123 - una fusión en el mass gap"
    assert respuesta.json()["fuente_titulo"] == FUENTE["fuente_titulo"]

    [nota] = _notas(vault)
    assert nota.name == "GW231123 - una fusión en el mass gap.md"
    texto = nota.read_text(encoding="utf-8")
    _, cabecera, cuerpo = texto.split("---\n", 2)
    datos = yaml.safe_load(cabecera)
    assert datos["type"] == "literature"
    assert datos["fuente_titulo"] == FUENTE["fuente_titulo"]
    assert datos["fuente_tipo"] == "paper"
    assert datos["autor"] == FUENTE["autor"]
    assert datos["status"] == "leido"
    assert datos["tags"] == ["voz-del-cosmos"]
    assert datos["fecha"] is not None
    # Las tres secciones del `CLAUDE.md` de la carpeta, y la fórmula intacta.
    assert "## Resumen\n\nLa fusión más masiva observada: $M \\approx 225\\,M_\\odot$." in cuerpo
    assert "Fuente: https://arxiv.org/abs/2507.08219" in cuerpo
    assert "## Nivel de confianza científica\n\nResultado preliminar." in cuerpo
    assert "## Relacionado\n\n- [[MOC-VozDelCosmos]]" in cuerpo


def test_la_nota_creada_aparece_en_el_respaldo(cliente: TestClient):
    """Lo que escribe este módulo lo lee el otro: si no, no serviría."""
    _entrar_como(cliente)
    cliente.post("/api/fuentes", json=FUENTE)

    notas = cliente.get("/api/respaldo").json()["notas"]

    assert [n["archivo"] for n in notas] == ["GW231123 - una fusión en el mass gap"]


def test_sin_resumen_queda_por_leer_y_sin_autor_no_lleva_autor(cliente: TestClient, vault: Path):
    _entrar_como(cliente)

    cliente.post("/api/fuentes", json={**FUENTE, "resumen": "  ", "autor": ""})

    datos = yaml.safe_load(_notas(vault)[0].read_text(encoding="utf-8").split("---\n")[1])
    assert datos["status"] == "por-leer"
    assert "autor" not in datos


def test_sin_nombre_la_nota_se_llama_como_la_fuente_sin_lo_prohibido(
    cliente: TestClient, vault: Path
):
    """La limpieza del ADR 0007: ni `:` ni `/`, que sacaría la nota de la carpeta."""
    _entrar_como(cliente)

    cliente.post(
        "/api/fuentes",
        json={**FUENTE, "nombre": "", "fuente_titulo": "../../GWTC-5.0: 1/3 [nuevo]"},
    )

    [nota] = _notas(vault)
    assert nota.name == "-..-GWTC-5.0 1-3 nuevo.md"


def test_un_doi_suelto_se_guarda_como_enlace(cliente: TestClient, vault: Path):
    _entrar_como(cliente)

    cliente.post("/api/fuentes", json={**FUENTE, "url": "10.3847/2041-8213/adc2f5"})

    assert "Fuente: https://doi.org/10.3847/2041-8213/adc2f5" in _notas(vault)[0].read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    "cambio",
    [
        {"fuente_titulo": "   "},
        {"fuente_titulo": "dos\nlíneas"},
        {"url": "arxiv punto org"},
        {"url": "javascript:alert(1)"},
        {"fuente_tipo": "libro"},
        {"confianza": "segura"},
    ],
)
def test_lo_que_no_vale_es_422_y_no_escribe(cliente: TestClient, vault: Path, cambio):
    _entrar_como(cliente)

    assert cliente.post("/api/fuentes", json={**FUENTE, **cambio}).status_code == 422
    assert _notas(vault) == []


# --- BB3: nunca pisa ---


def test_no_pisa_una_nota_que_ya_existe(cliente: TestClient, vault: Path):
    """La regla que sostiene el ADR 0019: crear, nunca editar."""
    existente = vault / "Investigacion" / "Recursos" / "GW231123 - una fusión en el mass gap.md"
    existente.write_text("escrita a mano por Johan", encoding="utf-8")
    _entrar_como(cliente)

    respuesta = cliente.post("/api/fuentes", json=FUENTE)

    assert respuesta.status_code == 409
    assert "otro nombre" in respuesta.json()["detail"]
    assert existente.read_text(encoding="utf-8") == "escrita a mano por Johan"


def test_el_modulo_solo_crea():
    """En el árbol sintáctico, como G2: ni mover, ni borrar, ni `write_text`,
    que pisa. La única escritura es el `open("x")`.
    """
    import ast

    from app import fuentes

    arbol = ast.parse(Path(fuentes.__file__).read_text(encoding="utf-8"))
    prohibidos = {"write_text", "write_bytes", "mkdir", "unlink", "rename", "replace", "touch"}
    llamadas = [
        n for n in ast.walk(arbol) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    ]

    assert [n.func.attr for n in llamadas if n.func.attr in prohibidos] == []
    modos = [n.args[0].value for n in llamadas if n.func.attr == "open"]
    assert modos == ["x"]


def test_sin_vault_es_409_y_lo_dice(cliente: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(respaldo, "carpeta_configurada", lambda: None)
    _entrar_como(cliente)

    respuesta = cliente.post("/api/fuentes", json=FUENTE)

    assert respuesta.status_code == 409
    assert "vault" in respuesta.json()["detail"]


# --- BB4: enlazada a la pieza ---


def test_queda_enlazada_a_la_pieza_desde_la_que_se_crea(cliente: TestClient, sesion_db: Session):
    pieza = Pieza(titulo="El mass gap", creada_por="johan", respaldo=["Otra nota"])
    sesion_db.add(pieza)
    sesion_db.commit()
    _entrar_como(cliente)

    cliente.post("/api/fuentes", json={**FUENTE, "pieza_id": pieza.id})

    sesion_db.refresh(pieza)
    assert pieza.respaldo == ["Otra nota", "GW231123 - una fusión en el mass gap"]


def test_con_una_pieza_que_no_existe_es_404_y_no_escribe(cliente: TestClient, vault: Path):
    _entrar_como(cliente)

    assert cliente.post("/api/fuentes", json={**FUENTE, "pieza_id": 999_999}).status_code == 404
    assert _notas(vault) == []
