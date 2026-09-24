"""Criterios Q1–Q5 y R1–R4 — la carpeta de la pieza en Syncthing y sus
miniaturas (ADR 0010).

Como las del respaldo, las pruebas usan una carpeta de mentira en `tmp_path`,
con su `.stfolder`, y no la de Johan: lo que hay ahí se sincroniza con la
máquina del editor.
"""

import ast
import io
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app import main, material
from app.db import get_db
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"


@pytest.fixture
def compartida(tmp_path: Path) -> Path:
    base = tmp_path / "compartida"
    (base / material.MARCA_DE_SYNCTHING).mkdir(parents=True)
    return base


@pytest.fixture
def cliente(sesion_db: Session, compartida: Path, monkeypatch: pytest.MonkeyPatch):
    sembrar_usuarios(
        sesion_db,
        [
            Semilla(usuario="johan", password=CLAVE, rol="investigador"),
            Semilla(usuario="dathzon", password=CLAVE, rol="editor"),
        ],
    )
    monkeypatch.setattr(material, "carpeta_compartida", lambda: compartida)
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


def _ver(cliente: TestClient, pieza: Pieza) -> dict:
    respuesta = cliente.get(f"/api/piezas/{pieza.id}/carpeta")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _crear(cliente: TestClient, pieza: Pieza) -> dict:
    respuesta = cliente.post(f"/api/piezas/{pieza.id}/carpeta")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _miniatura(cliente: TestClient, pieza: Pieza, nombre: str):
    return cliente.get(
        f"/api/piezas/{pieza.id}/carpeta/miniatura", params={"nombre": nombre}
    )


def _carpeta_de(compartida: Path, pieza: Pieza) -> Path:
    carpeta = compartida / f"{pieza.id} - Las Pléyades"
    carpeta.mkdir()
    return carpeta


# --- Q1: la carpeta compartida es opcional ---


def test_sin_carpeta_configurada_el_panel_dice_por_que(
    cliente: TestClient, pieza: Pieza, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(material, "carpeta_compartida", lambda: None)
    _entrar_como(cliente)

    for estado in (_ver(cliente, pieza), _crear(cliente, pieza)):
        assert estado["motivo"]
        assert estado["carpeta"] is None
        assert estado["archivos"] == []


def test_en_una_carpeta_que_no_es_de_syncthing_no_se_crea_nada(
    cliente: TestClient, pieza: Pieza, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Una errata en el `.env` y Docker monta una carpeta vacía. Lo que la app
    creara ahí no le llegaría al editor, así que ni lo intenta.
    """
    errata = tmp_path / "errata"
    errata.mkdir()
    monkeypatch.setattr(material, "carpeta_compartida", lambda: errata)
    _entrar_como(cliente)

    estado = _crear(cliente, pieza)

    assert material.MARCA_DE_SYNCTHING in estado["motivo"]
    assert list(errata.iterdir()) == []


# --- Q2: `<id> - <título>`, encontrada por el número ---


def test_la_carpeta_se_llama_id_y_titulo(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    _entrar_como(cliente)

    estado = _crear(cliente, pieza)

    assert estado["carpeta"] == f"{pieza.id} - Las Pléyades"
    assert (compartida / estado["carpeta"]).is_dir()


@pytest.mark.parametrize("usuario", ["johan", "dathzon"])
def test_la_crea_cualquiera_de_los_dos(cliente: TestClient, pieza: Pieza, usuario: str):
    _entrar_como(cliente, usuario)

    assert _crear(cliente, pieza)["carpeta"] == f"{pieza.id} - Las Pléyades"


def test_la_encuentra_por_el_numero_aunque_cambie_el_titulo(
    cliente: TestClient, pieza: Pieza, compartida: Path, sesion_db: Session
):
    """Y no crea otra: la app no renombra la carpeta (ADR 0010)."""
    _entrar_como(cliente)
    _crear(cliente, pieza)
    pieza.titulo = "El cúmulo abierto M45"
    sesion_db.flush()

    assert _ver(cliente, pieza)["carpeta"] == f"{pieza.id} - Las Pléyades"
    assert _crear(cliente, pieza)["carpeta"] == f"{pieza.id} - Las Pléyades"
    assert len(list(compartida.glob(f"{pieza.id} - *"))) == 1


def test_otra_pieza_cuyo_numero_empieza_igual_no_cuenta(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """El número se compara con su separador: `1 - ` no es prefijo de `12 - `."""
    (compartida / f"{pieza.id}2 - Otra pieza").mkdir()
    _entrar_como(cliente)

    assert _ver(cliente, pieza) == {"motivo": None, "carpeta": None, "archivos": []}


def test_dos_carpetas_con_el_mismo_numero_se_reportan_y_no_se_crea_otra(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """ADR 0010: la app no adivina cuál es la buena, dice que hay dos."""
    (compartida / f"{pieza.id} - Las Pléyades").mkdir()
    (compartida / f"{pieza.id} - Pléyades (copia)").mkdir()
    _entrar_como(cliente)

    estado = _crear(cliente, pieza)

    assert "Hay 2 carpetas" in estado["motivo"]
    assert estado["carpeta"] is None
    assert len(list(compartida.glob(f"{pieza.id} - *"))) == 2


@pytest.mark.parametrize(
    ("titulo", "nombre"),
    [
        ("¿Qué es un púlsar?", "¿Qué es un púlsar"),
        ('Luz: ¿"onda" o <partícula>?', "Luz ¿onda o partícula"),
        ("Hasta aquí. ", "Hasta aquí"),
        ("???", "sin título"),
        ("../../fuera", "fuera"),
    ],
)
def test_el_titulo_pierde_lo_que_windows_no_admite(titulo: str, nombre: str):
    pieza = Pieza(id=7, titulo=titulo, creada_por="johan")

    assert material.nombre_de_carpeta(pieza) == f"7 - {nombre}"


# --- Q3: el listado ---


def test_sin_carpeta_de_la_pieza_se_ofrece_crearla(cliente: TestClient, pieza: Pieza):
    """Ni motivo ni carpeta: es el estado en el que el panel ofrece el botón."""
    _entrar_como(cliente)

    assert _ver(cliente, pieza) == {"motivo": None, "carpeta": None, "archivos": []}


def test_lista_los_archivos_con_nombre_tamano_y_fecha(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """En el orden del explorador de Windows, sin distinguir mayúsculas."""
    carpeta = compartida / f"{pieza.id} - Las Pléyades"
    carpeta.mkdir()
    (carpeta / "Referencia.png").write_bytes(bytes(100))
    (carpeta / "boceto.psd").write_bytes(bytes(10))
    _entrar_como(cliente)

    archivos = _ver(cliente, pieza)["archivos"]

    assert [a["nombre"] for a in archivos] == ["boceto.psd", "Referencia.png"]
    assert [a["tamano"] for a in archivos] == [10, 100]
    modificado = datetime.fromtimestamp((carpeta / "Referencia.png").stat().st_mtime, UTC)
    assert datetime.fromisoformat(archivos[1]["modificado"]) == modificado


@pytest.mark.parametrize("metodo", ["GET", "POST"])
def test_la_carpeta_de_una_pieza_que_no_existe_es_404(
    cliente: TestClient, compartida: Path, metodo: str
):
    _entrar_como(cliente)

    respuesta = cliente.request(metodo, "/api/piezas/999999/carpeta")

    assert respuesta.status_code == 404
    assert list(compartida.glob("999999*")) == []


# --- Q4: nada fuera de la carpeta de la pieza ---


def test_un_titulo_con_dos_puntos_no_sale_de_la_compartida(
    cliente: TestClient, compartida: Path, sesion_db: Session
):
    pieza = Pieza(titulo="../../fuera", creada_por="johan")
    sesion_db.add(pieza)
    sesion_db.flush()
    _entrar_como(cliente)

    estado = _crear(cliente, pieza)

    assert (compartida / estado["carpeta"]).is_dir()
    assert [p.name for p in compartida.parent.iterdir()] == ["compartida"]


def test_no_lista_un_enlace_que_apunte_fuera(
    cliente: TestClient, pieza: Pieza, compartida: Path, tmp_path: Path
):
    """Como G3: `resolve()` sigue el enlace sin avisar. Ni el tamaño de lo que
    hay al otro lado sale en el listado.
    """
    secreto = tmp_path / "diario.md"
    secreto.write_text("fuera del alcance", encoding="utf-8")
    carpeta = compartida / f"{pieza.id} - Las Pléyades"
    carpeta.mkdir()
    try:
        (carpeta / "atajo.md").symlink_to(secreto)
    except (OSError, NotImplementedError):
        pytest.skip("el sistema de archivos no permite enlaces simbólicos")
    _entrar_como(cliente)

    assert _ver(cliente, pieza)["archivos"] == []


def test_una_carpeta_de_pieza_que_apunta_fuera_no_cuenta(
    cliente: TestClient, pieza: Pieza, compartida: Path, tmp_path: Path
):
    fuera = tmp_path / "fuera"
    fuera.mkdir()
    (fuera / "secreto.png").write_bytes(bytes(10))
    try:
        (compartida / f"{pieza.id} - Las Pléyades").symlink_to(
            fuera, target_is_directory=True
        )
    except (OSError, NotImplementedError):
        pytest.skip("el sistema de archivos no permite enlaces simbólicos")
    _entrar_como(cliente)

    estado = _ver(cliente, pieza)

    assert estado["carpeta"] is None
    assert estado["archivos"] == []


# --- Q5: lo único que se escribe es la carpeta de la pieza ---


def test_la_unica_escritura_del_modulo_es_el_mkdir_de_la_carpeta():
    """Q5 en el árbol sintáctico, como G2. Si algún día hace falta otra
    escritura, esta prueba obliga a decidirlo a propósito.
    """
    fuente = Path(material.__file__).read_text(encoding="utf-8")
    escrituras = {
        "write_text", "write_bytes", "open", "touch", "mkdir", "unlink",
        "rmdir", "rename", "replace", "symlink_to", "hardlink_to",
    }

    llamadas = [
        nodo.func.attr
        for nodo in ast.walk(ast.parse(fuente))
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr in escrituras
        # El `open` de Pillow lee la imagen de la miniatura (R1); no escribe.
        and ast.unparse(nodo.func) != "Image.open"
    ]

    assert llamadas == ["mkdir"]


def test_ver_y_crear_no_tocan_ningun_archivo(
    cliente: TestClient, pieza: Pieza, compartida: Path, sesion_db: Session
):
    """Q5 en el comportamiento: con archivos de verdad dentro, ver, crear y
    pedir miniaturas solo añade la carpeta de la pieza que no la tenía. R2:
    la miniatura no se guarda en ninguna parte.
    """
    otra = Pieza(titulo="Otra pieza", creada_por="johan")
    sesion_db.add(otra)
    sesion_db.flush()
    suya = compartida / f"{otra.id} - Otra pieza"
    suya.mkdir()
    Image.new("RGB", (800, 600), (30, 60, 90)).save(suya / "diseño final.png")
    antes = {p: p.stat().st_mtime_ns for p in compartida.rglob("*")}
    _entrar_como(cliente)

    for una in (otra, pieza):
        _ver(cliente, una)
        _crear(cliente, una)
    assert _miniatura(cliente, otra, "diseño final.png").status_code == 200

    despues = {p: p.stat().st_mtime_ns for p in compartida.rglob("*")}
    assert set(despues) - set(antes) == {compartida / f"{pieza.id} - Las Pléyades"}
    assert {p: despues[p] for p in antes} == antes


# --- R: miniaturas ---


@pytest.mark.parametrize(
    ("nombre", "formato"),
    [
        ("foto.jpg", "JPEG"),
        ("CAMARA.JPEG", "JPEG"),
        ("logo.png", "PNG"),
        ("pin.webp", "WEBP"),
    ],
)
def test_jpg_png_y_webp_tienen_miniatura(
    cliente: TestClient, pieza: Pieza, compartida: Path, nombre: str, formato: str
):
    """R1, siguiendo la URL que da el listado, como hará el navegador."""
    carpeta = _carpeta_de(compartida, pieza)
    Image.new("RGB", (1600, 1200), (40, 90, 160)).save(carpeta / nombre, formato)
    _entrar_como(cliente)

    (archivo,) = _ver(cliente, pieza)["archivos"]
    respuesta = cliente.get(archivo["miniatura"])

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "image/webp"
    assert Image.open(io.BytesIO(respuesta.content)).size == (400, 300)


def test_una_imagen_grande_de_verdad_cabe_en_el_tope(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """R3. Ruido con transparencia, lo que peor se comprime: a la calidad de
    partida su miniatura pesaría 245 kB, así que la prueba obliga a bajarla.
    """
    carpeta = _carpeta_de(compartida, pieza)
    lado = 2000
    ruido = Image.frombytes("RGBA", (lado, lado), os.urandom(lado * lado * 4))
    ruido.save(carpeta / "ruido.png", compress_level=1)
    assert (carpeta / "ruido.png").stat().st_size > 15_000_000
    _entrar_como(cliente)

    respuesta = _miniatura(cliente, pieza, "ruido.png")

    assert respuesta.status_code == 200
    assert len(respuesta.content) < material.TOPE_DE_MINIATURA
    assert Image.open(io.BytesIO(respuesta.content)).size == (400, 400)


def test_la_miniatura_se_guarda_mientras_el_archivo_no_cambie(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """R2: la caché del navegador es eterna porque la URL cambia con el
    archivo. `private`, porque la miniatura pide sesión.
    """
    carpeta = _carpeta_de(compartida, pieza)
    Image.new("RGB", (800, 600)).save(carpeta / "foto.png")
    _entrar_como(cliente)
    antes = _ver(cliente, pieza)["archivos"][0]["miniatura"]

    respuesta = cliente.get(antes)
    os.utime(carpeta / "foto.png", ns=(1_700_000_000_000_000_000,) * 2)
    despues = _ver(cliente, pieza)["archivos"][0]["miniatura"]

    assert "immutable" in respuesta.headers["cache-control"]
    assert "private" in respuesta.headers["cache-control"]
    assert despues != antes


def test_los_demas_archivos_no_tienen_miniatura(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """R4: se listan, con su tamaño y su fecha, pero sin miniatura."""
    carpeta = _carpeta_de(compartida, pieza)
    (carpeta / "boceto.psd").write_bytes(bytes(10))
    _entrar_como(cliente)

    assert _ver(cliente, pieza)["archivos"][0]["miniatura"] is None
    assert _miniatura(cliente, pieza, "boceto.psd").status_code == 404


def test_la_foto_del_movil_no_sale_tumbada(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """El móvil guarda la foto de lado y apunta en el EXIF cómo girarla."""
    carpeta = _carpeta_de(compartida, pieza)
    exif = Image.Exif()
    exif[0x0112] = 6  # Orientation: girar 90° para verla
    Image.new("RGB", (1200, 600)).save(carpeta / "movil.jpg", exif=exif)
    _entrar_como(cliente)

    respuesta = _miniatura(cliente, pieza, "movil.jpg")

    ancho, alto = Image.open(io.BytesIO(respuesta.content)).size
    assert alto > ancho


def test_un_png_de_16_bits_no_sale_blanco(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """Pillow recorta a 255 al pasar 16 bits a 8, y un degradado de 0 a 65535
    saldría blanco casi entero. Se reescala entre su mínimo y su máximo.
    """
    carpeta = _carpeta_de(compartida, pieza)
    degradado = Image.new("I;16", (1000, 10))
    degradado.putdata([(x * 65535) // 999 for _ in range(10) for x in range(1000)])
    degradado.save(carpeta / "nebulosa.png")
    _entrar_como(cliente)

    respuesta = _miniatura(cliente, pieza, "nebulosa.png")

    gris = Image.open(io.BytesIO(respuesta.content)).convert("L")
    izquierda, derecha = gris.getpixel((2, 2)), gris.getpixel((397, 2))
    assert izquierda < 30 and derecha > 225


def test_una_imagen_que_no_se_puede_leer_es_404(
    cliente: TestClient, pieza: Pieza, compartida: Path
):
    """Un archivo a medio copiar, o que no es lo que dice su extensión."""
    carpeta = _carpeta_de(compartida, pieza)
    (carpeta / "roto.png").write_bytes(b"no soy un png")
    _entrar_como(cliente)

    assert _miniatura(cliente, pieza, "roto.png").status_code == 404


def test_sin_carpeta_de_la_pieza_no_hay_miniatura(cliente: TestClient, pieza: Pieza):
    _entrar_como(cliente)

    assert _miniatura(cliente, pieza, "foto.png").status_code == 404


@pytest.mark.parametrize("nombre", ["../fuera.png", "../../fuera.png", "a/../../fuera.png"])
def test_la_miniatura_no_sale_de_la_carpeta_de_la_pieza(
    cliente: TestClient, pieza: Pieza, compartida: Path, tmp_path: Path, nombre: str
):
    """Q4 con un nombre que llega en la URL. `../fuera.png` sigue dentro de la
    carpeta compartida, pero no de la de esta pieza.
    """
    _carpeta_de(compartida, pieza)
    Image.new("RGB", (100, 100)).save(compartida / "fuera.png")
    Image.new("RGB", (100, 100)).save(tmp_path / "fuera.png")
    _entrar_como(cliente)

    assert _miniatura(cliente, pieza, nombre).status_code == 404


def test_la_miniatura_no_sigue_un_enlace_que_apunte_fuera(
    cliente: TestClient, pieza: Pieza, compartida: Path, tmp_path: Path
):
    secreto = tmp_path / "secreto.png"
    Image.new("RGB", (100, 100)).save(secreto)
    carpeta = _carpeta_de(compartida, pieza)
    try:
        (carpeta / "atajo.png").symlink_to(secreto)
    except (OSError, NotImplementedError):
        pytest.skip("el sistema de archivos no permite enlaces simbólicos")
    _entrar_como(cliente)

    assert _miniatura(cliente, pieza, "atajo.png").status_code == 404
