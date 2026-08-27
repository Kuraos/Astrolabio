"""Criterios G1–G4 y H4 — el respaldo científico se lee, nunca se escribe.

Las pruebas usan un vault de mentira en `tmp_path`, no el de Johan: una suite
que depende de su carpeta personal no corre en la CI, no corre en la máquina
del editor, y falla el día que él reorganiza sus notas.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main, respaldo
from app.db import get_db
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

# El caso que hace inviable partir la línea por el primer `:` — es el título
# real de una de las notas del vault.
NOTA_CON_DOS_PUNTOS = """\
---
type: literature
cssclasses: [vh-literature]
fuente_titulo: "GWTC-5.0: Updated LIGO–Virgo–KAGRA Catalog sets new records"
fuente_tipo: articulo
autor: Colaboración LIGO-Virgo-KAGRA (LIGO Lab, Caltech)
status: leido
fecha: 2026-07-27
tags: [voz-del-cosmos]
---

## Resumen

Texto que no debería aparecer en el listado.
"""

NOTA_MINIMA = """\
---
type: literature
fuente_titulo: Una fuente sin autor declarado
fecha: 2026-08-01
tags: [voz-del-cosmos]
---

## Resumen
"""

NOTA_QUE_NO_ES_RESPALDO = """\
---
type: contenido
tema: Ondas gravitacionales
---

## Guion
"""


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """Reproduce la estructura real de `03-Negocios/Voz-del-Cosmos/`."""
    recursos = tmp_path / "Investigacion" / "Recursos"
    recursos.mkdir(parents=True)

    (recursos / "GWTC-5.md").write_text(NOTA_CON_DOS_PUNTOS, encoding="utf-8")
    (recursos / "Sin-autor.md").write_text(NOTA_MINIMA, encoding="utf-8")
    (recursos / "No-es-respaldo.md").write_text(
        NOTA_QUE_NO_ES_RESPALDO, encoding="utf-8"
    )

    return tmp_path


# --- G1 ---


def test_lista_las_notas_de_respaldo_con_su_frontmatter(vault: Path):
    notas = respaldo.listar_respaldo(vault)

    por_archivo = {n.archivo: n for n in notas}
    assert set(por_archivo) == {"GWTC-5", "Sin-autor"}

    gwtc = por_archivo["GWTC-5"]
    assert gwtc.autor == "Colaboración LIGO-Virgo-KAGRA (LIGO Lab, Caltech)"
    assert str(gwtc.fecha) == "2026-07-27"


def test_el_titulo_conserva_los_dos_puntos(vault: Path):
    """El motivo de usar un parser de YAML y no partir la línea a mano."""
    gwtc = next(n for n in respaldo.listar_respaldo(vault) if n.archivo == "GWTC-5")

    assert gwtc.fuente_titulo == (
        "GWTC-5.0: Updated LIGO–Virgo–KAGRA Catalog sets new records"
    )


def test_ignora_lo_que_no_sea_literature(vault: Path):
    """El ADR 0001 solo le da autoridad al vault sobre `literature`. Una nota
    `contenido` que apareciera aquí sería la copia generada por Astrolabio
    leyéndose a sí misma.
    """
    archivos = {n.archivo for n in respaldo.listar_respaldo(vault)}

    assert "No-es-respaldo" not in archivos


def test_una_nota_sin_autor_no_rompe_el_listado(vault: Path):
    sin_autor = next(
        n for n in respaldo.listar_respaldo(vault) if n.archivo == "Sin-autor"
    )

    assert sin_autor.autor is None
    assert sin_autor.fuente_titulo == "Una fuente sin autor declarado"


def test_el_cuerpo_de_la_nota_no_sale_en_el_listado(vault: Path):
    """El listado es un índice. Traerse el texto completo de cada nota sería
    mover el vault entero a la API por si acaso.
    """
    serializado = str([n.model_dump() for n in respaldo.listar_respaldo(vault)])

    assert "no debería aparecer" not in serializado


# --- G3: no se sale de la carpeta ---


def test_no_lee_a_traves_de_un_enlace_que_apunte_fuera(vault: Path, tmp_path: Path):
    """§2.5. Un enlace simbólico dentro de la carpeta es la vía real de fuga:
    `resolve()` lo sigue sin avisar, y al otro lado está el resto del vault
    personal — el diario incluido.
    """
    secreto = tmp_path.parent / "fuera-del-alcance.md"
    secreto.write_text(
        "---\ntype: literature\nfuente_titulo: No deberia verse\n---\n",
        encoding="utf-8",
    )

    enlace = vault / "Investigacion" / "Recursos" / "atajo.md"
    try:
        enlace.symlink_to(secreto)
    except (OSError, NotImplementedError):
        pytest.skip("el sistema de archivos no permite enlaces simbólicos")

    titulos = {n.fuente_titulo for n in respaldo.listar_respaldo(vault)}

    assert "No deberia verse" not in titulos


def test_una_ruta_con_dos_puntos_no_escapa(vault: Path):
    assert respaldo.dentro_de(vault, vault / "Investigacion" / ".." / "..") is False
    assert respaldo.dentro_de(vault, vault / "Investigacion" / "Recursos") is True


# --- G4: el vault puede no estar ---


def test_sin_carpeta_configurada_no_revienta():
    """El vault es de Johan y vive en su máquina. El taller no puede depender
    de que esté montado: el editor entra igual y la aplicación funciona.
    """
    estado = respaldo.estado_del_respaldo(None)

    assert estado.disponible is False
    assert estado.notas == []
    assert estado.motivo


def test_una_carpeta_que_no_existe_se_reporta_sin_error(tmp_path: Path):
    estado = respaldo.estado_del_respaldo(tmp_path / "no-existe")

    assert estado.disponible is False
    assert estado.motivo


def test_con_carpeta_valida_queda_disponible(vault: Path):
    estado = respaldo.estado_del_respaldo(vault)

    assert estado.disponible is True
    assert len(estado.notas) == 2


# --- G2 y H4: la API ---


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


def _entrar_como(cliente: TestClient, usuario: str) -> None:
    assert (
        cliente.post(
            "/api/auth/login", json={"usuario": usuario, "password": CLAVE}
        ).status_code
        == 200
    )


def test_el_investigador_ve_el_respaldo(cliente: TestClient):
    _entrar_como(cliente, "johan")

    respuesta = cliente.get("/api/respaldo")

    assert respuesta.status_code == 200
    assert respuesta.json()["disponible"] is True
    assert len(respuesta.json()["notas"]) == 2


def test_el_editor_no_ve_el_respaldo(cliente: TestClient):
    """H4. El ADR 0001 le da `literature` a Johan y solo a Johan; el vault es
    su carpeta personal. 403, no un panel escondido (§2.3).
    """
    _entrar_como(cliente, "dathzon")

    assert cliente.get("/api/respaldo").status_code == 403


def test_sin_sesion_el_respaldo_responde_401(cliente: TestClient):
    assert cliente.get("/api/respaldo").status_code == 401


# --- G2: solo lectura ---


def test_ninguna_ruta_del_modulo_escribe_en_el_vault():
    """G2, comprobado en el árbol sintáctico: el módulo que lee el vault no
    puede contener escrituras. El exportador de la Fase I vivirá en otro
    módulo y con su propia carpeta, para que esta separación siga siendo
    visible en el código y no solo en la intención.
    """
    import ast

    fuente = Path(respaldo.__file__).read_text(encoding="utf-8")
    prohibidos = {"write_text", "write_bytes", "mkdir", "unlink", "rename", "touch"}

    culpables = [
        f"{nodo.func.attr}:{nodo.lineno}"
        for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr in prohibidos
    ]

    assert culpables == []


def test_el_listado_no_modifica_la_carpeta(vault: Path):
    antes = {p: p.stat().st_mtime_ns for p in vault.rglob("*") if p.is_file()}

    respaldo.listar_respaldo(vault)

    despues = {p: p.stat().st_mtime_ns for p in vault.rglob("*") if p.is_file()}
    assert antes == despues
