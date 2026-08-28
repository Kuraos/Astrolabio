"""Criterios I1–I5 — el exportador escribe en el vault, en una sola dirección.

La regla del ADR 0001 es que `contenido` se edita **solo** en Astrolabio y el
vault recibe una copia marcada como generada. Estas pruebas vigilan las dos
mitades: que la copia salga bien formada, y que la aplicación no invada nada
que no le corresponda.
"""

from datetime import date
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import exportador, respaldo
from app.db import get_db
from app import main
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

MOC_INICIAL = """\
---
type: moc
tags: [moc, voz-del-cosmos]
---

## Notas de investigación

- [[Una nota de respaldo]]

## Enlaces fijos

- [[Home]]
"""


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    (tmp_path / "Contenido").mkdir()
    (tmp_path / "Investigacion" / "Recursos").mkdir(parents=True)
    (tmp_path / "MOC-VozDelCosmos.md").write_text(MOC_INICIAL, encoding="utf-8")
    return tmp_path


@pytest.fixture
def pieza(sesion_db: Session) -> Pieza:
    p = Pieza(
        titulo="Las Pleyades",
        creada_por="johan",
        guion="## Guion\n\nUna masa solar es $M_\\odot$.\n",
        formato="video",
        tema="Cumulos abiertos",
        plataforma="YouTube",
        respaldo=["GWTC-5"],
    )
    sesion_db.add(p)
    sesion_db.flush()
    return p


def _frontmatter(texto: str) -> dict:
    return yaml.safe_load(texto.split("---", 2)[1])


# --- I1, I2: la nota generada ---


def test_exporta_a_la_carpeta_de_contenido(vault: Path, pieza: Pieza):
    destino = exportador.exportar(pieza, vault)

    assert destino == vault / "Contenido" / "Las Pleyades.md"
    assert destino.is_file()


def test_el_frontmatter_cumple_la_plantilla(vault: Path, pieza: Pieza):
    """El ADR 0001 dice que la nota generada debe pasar la auditoría del vault
    sin hallazgos, y eso es criterio de aceptación, no un detalle.
    """
    datos = _frontmatter(exportador.exportar(pieza, vault).read_text(encoding="utf-8"))

    assert datos["type"] == "contenido"
    # Fecha sin comillas: un `date` de YAML, como en la plantilla escrita a mano.
    assert isinstance(datos["fecha"], date)
    assert datos["formato"] == "video"
    assert datos["tema"] == "Cumulos abiertos"
    assert datos["plataforma"] == "YouTube"
    assert datos["tags"] == ["voz-del-cosmos"]
    assert datos["investigacion"] == ["GWTC-5"]
    assert "status" in datos


def test_la_nota_se_declara_generada(vault: Path, pieza: Pieza):
    """I2. Dentro de seis meses tiene que ser evidente cuál copia es la buena."""
    texto = exportador.exportar(pieza, vault).read_text(encoding="utf-8")

    assert _frontmatter(texto)["fuente"] == "astrolabio"
    assert exportador.MARCA in texto


def test_el_guion_viaja_con_su_latex(vault: Path, pieza: Pieza):
    texto = exportador.exportar(pieza, vault).read_text(encoding="utf-8")

    assert r"$M_\odot$" in texto


def test_el_respaldo_sale_como_wikilinks(vault: Path, pieza: Pieza):
    """La sección enlazada y el campo del frontmatter tienen que coincidir: es
    lo que pide el `CLAUDE.md` de la carpeta.
    """
    texto = exportador.exportar(pieza, vault).read_text(encoding="utf-8")

    assert "[[GWTC-5]]" in texto
    assert _frontmatter(texto)["investigacion"] == ["GWTC-5"]


# --- I4: idempotencia ---


def test_reexportar_actualiza_en_vez_de_duplicar(vault: Path, pieza: Pieza):
    exportador.exportar(pieza, vault)
    pieza.guion = "## Guion\n\nTexto corregido.\n"
    destino = exportador.exportar(pieza, vault)

    assert len(list((vault / "Contenido").glob("*.md"))) == 1
    assert "Texto corregido" in destino.read_text(encoding="utf-8")


def test_cambiar_el_titulo_renombra_la_nota(vault: Path, pieza: Pieza):
    """El nombre sale del título (ADR 0007) y el título puede cambiar. Sin
    esto quedarían dos notas contradictorias sobre la misma pieza.
    """
    exportador.exportar(pieza, vault)
    pieza.titulo = "Las Pleyades, revisado"
    exportador.exportar(pieza, vault)

    archivos = sorted(p.name for p in (vault / "Contenido").glob("*.md"))
    assert archivos == ["Las Pleyades, revisado.md"]


# --- I5: no pisa lo que no es suyo ---


def test_se_niega_a_pisar_una_nota_escrita_a_mano(vault: Path, pieza: Pieza):
    """Sin la marca de generada, el archivo lo escribió una persona. La regla
    de una sola dirección no autoriza a Astrolabio a decidir que su versión
    es la buena.
    """
    a_mano = vault / "Contenido" / "Las Pleyades.md"
    a_mano.write_text("---\ntype: contenido\n---\n\nEscrito a mano.\n", encoding="utf-8")

    with pytest.raises(exportador.NotaAjena):
        exportador.exportar(pieza, vault)

    assert "Escrito a mano" in a_mano.read_text(encoding="utf-8")


def test_no_escribe_fuera_de_contenido_y_el_moc(vault: Path, pieza: Pieza):
    otros = {
        p: p.stat().st_mtime_ns
        for p in vault.rglob("*")
        if p.is_file() and "Contenido" not in p.parts and p.name != "MOC-VozDelCosmos.md"
    }

    exportador.exportar(pieza, vault)

    for archivo, momento in otros.items():
        assert archivo.stat().st_mtime_ns == momento


# --- El MOC ---


def test_enlaza_la_pieza_desde_el_moc(vault: Path, pieza: Pieza):
    exportador.exportar(pieza, vault)

    moc = (vault / "MOC-VozDelCosmos.md").read_text(encoding="utf-8")
    assert exportador.SECCION_MOC in moc
    assert "[[Las Pleyades]]" in moc


def test_no_duplica_el_enlace_al_reexportar(vault: Path, pieza: Pieza):
    exportador.exportar(pieza, vault)
    exportador.exportar(pieza, vault)

    moc = (vault / "MOC-VozDelCosmos.md").read_text(encoding="utf-8")
    assert moc.count("[[Las Pleyades]]") == 1


def test_no_toca_las_secciones_escritas_a_mano(vault: Path, pieza: Pieza):
    """La sección de Astrolabio es suya; el resto del MOC es de Johan."""
    exportador.exportar(pieza, vault)

    moc = (vault / "MOC-VozDelCosmos.md").read_text(encoding="utf-8")
    assert "## Notas de investigación" in moc
    assert "- [[Una nota de respaldo]]" in moc
    assert "## Enlaces fijos" in moc
    assert "- [[Home]]" in moc


# --- La API (J3 por debajo) ---


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


def test_exportar_devuelve_donde_quedo_el_archivo(cliente: TestClient, pieza: Pieza):
    """J3: la acción tiene resultado visible. «Exportado» sin decir dónde
    obliga a ir a buscarlo al vault para saber si funcionó.
    """
    _entrar_como(cliente, "johan")

    respuesta = cliente.post(f"/api/piezas/{pieza.id}/exportar")

    assert respuesta.status_code == 200
    assert respuesta.json()["archivo"].endswith("Las Pleyades.md")


def test_el_editor_no_exporta(cliente: TestClient, pieza: Pieza):
    """El destino es el vault personal de Johan (ADR 0001)."""
    _entrar_como(cliente, "dathzon")

    assert cliente.post(f"/api/piezas/{pieza.id}/exportar").status_code == 403


def test_sin_vault_configurado_lo_dice_sin_reventar(
    cliente: TestClient, pieza: Pieza, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(respaldo, "carpeta_configurada", lambda: None)
    _entrar_como(cliente, "johan")

    respuesta = cliente.post(f"/api/piezas/{pieza.id}/exportar")

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]


# --- Fidelidad a la plantilla del vault ---


def test_la_fecha_es_la_local_no_la_utc(vault: Path, sesion_db: Session):
    """`creada_en` se guarda en UTC. Una pieza creada a las 21:00 en Bogotá
    son las 02:00 UTC del día siguiente, así que exportar la fecha en UTC
    adelanta un día toda pieza hecha de noche — silenciosamente.
    """
    from datetime import UTC, datetime

    p = Pieza(
        titulo="Creada de noche",
        creada_por="johan",
        # 02:00 UTC = 21:00 del día anterior en Bogotá (UTC-5).
        creada_en=datetime(2026, 8, 28, 2, 0, tzinfo=UTC),
    )
    sesion_db.add(p)
    sesion_db.flush()

    datos = _frontmatter(exportador.exportar(p, vault).read_text(encoding="utf-8"))

    assert str(datos["fecha"]) == "2026-08-27"


def test_incluye_las_secciones_de_la_plantilla(vault: Path, pieza: Pieza):
    """La checklist de verificación es parte del flujo descrito en el
    `CLAUDE.md` de la carpeta. Perderla al exportar la borra del proceso.
    """
    texto = exportador.exportar(pieza, vault).read_text(encoding="utf-8")

    assert "## Verificación antes de publicar" in texto
    assert "## Notas de producción" in texto
    assert "Cada afirmación del guion tiene una nota de respaldo" in texto


def test_el_guion_queda_bajo_su_seccion_una_sola_vez(vault: Path, sesion_db: Session):
    p = Pieza(titulo="Sin encabezado", creada_por="johan", guion="Texto pelado.")
    sesion_db.add(p)
    sesion_db.flush()

    texto = exportador.exportar(p, vault).read_text(encoding="utf-8")

    assert texto.count("## Guion") == 1
    assert "Texto pelado." in texto


def test_no_duplica_el_encabezado_si_el_guion_ya_lo_trae(
    vault: Path, pieza: Pieza
):
    texto = exportador.exportar(pieza, vault).read_text(encoding="utf-8")

    assert texto.count("## Guion") == 1
