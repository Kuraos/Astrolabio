"""Criterios AN1–AN6 de la Fase 8 — el cuadro de materiales en la pieza.

Como las de Y, le pegan directamente a la API: qué valores admite el cuadro lo
decide el servidor, no el formulario (§2.3). Y la migración que lo trae se
prueba en los dos sentidos contra datos reales, porque es la primera que
cambia valores que ya estaban guardados.
"""

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

LISTAS = {
    "formato": ["carrusel", "post_individual", "short", "poster", "video_largo"],
    "proposito": ["divulgar", "promocionar", "educar", "noticia", "comunidad"],
    "nivel": ["basico", "avanzado"],
}


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
    p = Pieza(titulo="La luz de las estrellas muertas", creada_por="johan")
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


# --- AN1–AN3: tipo de pieza, propósito y nivel, de listas cerradas ---


@pytest.mark.parametrize(
    ("campo", "valor"), [(campo, valor) for campo, valores in LISTAS.items() for valor in valores]
)
def test_cada_valor_de_las_listas_se_acepta(
    cliente: TestClient, pieza: Pieza, campo: str, valor: str
):
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, **{campo: valor})

    assert respuesta.status_code == 200
    assert respuesta.json()[campo] == valor


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        # Los valores de antes de la Fase 8: la migración los convierte, y la
        # API ya no los admite.
        ("formato", "reel"),
        ("formato", "video"),
        # Las palabras de pantalla no son los identificadores.
        ("formato", "Video largo"),
        ("proposito", "Divulgar"),
        ("proposito", "entretener"),
        ("nivel", "intermedio"),
        ("nivel", ""),
    ],
)
def test_un_valor_fuera_de_la_lista_es_422(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, campo: str, valor: str
):
    """AN6. Y un 422 no escribe nada."""
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, **{campo: valor})

    assert respuesta.status_code == 422
    sesion_db.refresh(pieza)
    assert getattr(pieza, campo) is None


# --- AN4: el destino, una lista ---


def test_los_destinos_se_guardan_en_el_orden_de_la_lista_y_sin_repetir(
    cliente: TestClient, pieza: Pieza
):
    """Lo de TikTok va tal cual a Instagram: una pieza puede tener varios. El
    orden es el de la lista y no el de los clics, para que la misma pieza
    escriba siempre el mismo frontmatter.
    """
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, plataforma=["tiktok", "instagram", "tiktok"])

    assert respuesta.status_code == 200
    assert respuesta.json()["plataforma"] == ["instagram", "tiktok"]


def test_los_destinos_se_vacian_con_una_lista_vacia(
    cliente: TestClient, pieza: Pieza, sesion_db: Session
):
    pieza.plataforma = ["youtube"]
    sesion_db.flush()
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, plataforma=[])

    assert respuesta.status_code == 200
    assert respuesta.json()["plataforma"] == []


@pytest.mark.parametrize("destinos", [["facebook"], ["instagram", "Instagram"], "instagram"])
def test_un_destino_fuera_de_la_lista_es_422(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, destinos
):
    """Uno raro basta para rechazarlos todos, y una cadena suelta no es una
    lista.
    """
    _entrar_como(cliente)

    respuesta = _editar(cliente, pieza, plataforma=destinos)

    assert respuesta.status_code == 422
    sesion_db.refresh(pieza)
    assert pieza.plataforma == []


# --- AN5: el copy gráfico y el caption ---


def test_el_copy_grafico_guarda_cada_lamina_tal_cual(cliente: TestClient, pieza: Pieza):
    """En su orden, con la lámina en blanco que se reservó y con el LaTeX
    intacto: `\\nabla` empieza por `\\n`, como recuerda `test_guion.py`.
    """
    laminas = [
        "La luz que ves salió hace 8 minutos",
        "",
        r"$d = c\,t \approx 1{,}5 \times 10^{11}\,\mathrm{m}$ y $\nabla \cdot \mathbf{E} = 0$",
    ]
    _entrar_como(cliente)

    _editar(cliente, pieza, copy_grafico=laminas)
    leida = cliente.get(f"/api/piezas/{pieza.id}").json()

    assert leida["copy_grafico"] == laminas


def test_el_caption_guarda_emojis_y_hashtags(cliente: TestClient, pieza: Pieza):
    caption = "¿Sabías que el Sol que ves es de hace 8 minutos? ☀️🔭\n\n#astronomia #ciencia"
    _entrar_como(cliente)

    _editar(cliente, pieza, caption=caption)
    leida = cliente.get(f"/api/piezas/{pieza.id}").json()

    assert leida["caption"] == caption


def test_una_pieza_nace_con_el_cuadro_vacio(cliente: TestClient):
    """Crear con solo el título sigue funcionando (C2)."""
    _entrar_como(cliente)

    creada = cliente.post("/api/piezas", json={"titulo": "Nueva"}).json()

    assert creada["proposito"] is None
    assert creada["nivel"] is None
    assert creada["plataforma"] == []
    assert creada["copy_grafico"] == []
    assert creada["caption"] == ""


def test_una_pieza_puede_nacer_con_el_cuadro(cliente: TestClient):
    _entrar_como(cliente)

    respuesta = cliente.post(
        "/api/piezas",
        json={
            "titulo": "Nueva",
            "formato": "carrusel",
            "proposito": "educar",
            "nivel": "basico",
            "plataforma": ["tiktok", "instagram"],
        },
    )

    assert respuesta.status_code == 201
    creada = respuesta.json()
    assert (creada["formato"], creada["proposito"], creada["nivel"]) == (
        "carrusel",
        "educar",
        "basico",
    )
    assert creada["plataforma"] == ["instagram", "tiktok"]


# --- AN6: los dos roles editan el cuadro ---


def test_el_editor_edita_todo_el_cuadro(cliente: TestClient, pieza: Pieza):
    """Como el guion: los dos roles editan la pieza, y el cuadro no es la
    excepción que sí es el respaldo.
    """
    _entrar_como(cliente, "dathzon")

    respuesta = _editar(
        cliente,
        pieza,
        formato="poster",
        proposito="promocionar",
        nivel="avanzado",
        plataforma=["impreso"],
        copy_grafico=["Voz del Cosmos"],
        caption="Ya disponible",
    )

    assert respuesta.status_code == 200
    editada = respuesta.json()
    assert editada["formato"] == "poster"
    assert editada["plataforma"] == ["impreso"]
    assert editada["copy_grafico"] == ["Voz del Cosmos"]
    assert editada["caption"] == "Ya disponible"


# --- La migración, en los dos sentidos (AR1) ---

ANTERIOR = "e4237e4b450d"
AUTORA = "prueba-de-migracion"


@pytest.fixture
def base(engine_de_prueba, config_alembic):
    """La base de pruebas fuera de la transacción de cada prueba: la
    migración corre en la suya, y lo que se inserta aquí se confirma.

    Al acabar, pase lo que pase, sin las filas de aquí y otra vez en `head`:
    las pruebas siguientes cuentan con el esquema de ahora. Las filas se
    borran antes de subir, porque una que la migración no sabe convertir la
    detendría.
    """
    try:
        yield engine_de_prueba
    finally:
        with engine_de_prueba.begin() as conexion:
            conexion.execute(
                text("DELETE FROM pieza WHERE creada_por = :autora"), {"autora": AUTORA}
            )
        command.upgrade(config_alembic, "head")


def _insertar(engine, **columnas) -> int:
    """Una pieza por SQL, porque en la versión anterior el modelo no sirve."""
    nombres = ["titulo", "creada_por", *columnas]
    with engine.begin() as conexion:
        return conexion.execute(
            text(
                f"INSERT INTO pieza ({', '.join(nombres)})"
                f" VALUES ({', '.join(f':{n}' for n in nombres)}) RETURNING id"
            ),
            {"titulo": "x", "creada_por": AUTORA, **columnas},
        ).scalar_one()


def _leer(engine) -> dict[int, tuple]:
    with engine.connect() as conexion:
        filas = conexion.execute(
            text("SELECT id, formato, plataforma FROM pieza WHERE creada_por = :autora"),
            {"autora": AUTORA},
        )
        return {id_: (formato, plataforma) for id_, formato, plataforma in filas}


def _version(engine) -> str:
    with engine.connect() as conexion:
        return conexion.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def test_la_migracion_convierte_el_tipo_y_el_destino(base, config_alembic):
    """AN1 y AN4: cada valor viejo a su nuevo, y el destino, a una lista de
    uno sin distinguir mayúsculas ni espacios alrededor.
    """
    command.downgrade(config_alembic, ANTERIOR)
    esperado = {
        _insertar(base, formato="reel", plataforma="Instagram"): ("short", ["instagram"]),
        _insertar(base, formato="video", plataforma=" YouTube "): ("video_largo", ["youtube"]),
        _insertar(base, formato="post", plataforma=""): ("post_individual", []),
        _insertar(base, formato="carrusel", plataforma=None): ("carrusel", []),
        _insertar(base, formato=None, plataforma="TikTok"): (None, ["tiktok"]),
    }

    command.upgrade(config_alembic, "head")

    assert _leer(base) == esperado


@pytest.mark.parametrize(
    ("columnas", "nombrado"),
    [({"formato": "gif"}, "gif"), ({"plataforma": "Facebook"}, "Facebook")],
)
def test_un_valor_que_no_sabe_convertir_detiene_la_migracion(
    base, config_alembic, columnas: dict, nombrado: str
):
    """AN4: se detiene y lo nombra, en vez de perderlo. Y no deja nada a
    medias: la base sigue en la versión anterior, con el valor intacto.
    """
    command.downgrade(config_alembic, ANTERIOR)
    id_ = _insertar(base, **columnas)

    with pytest.raises(RuntimeError, match=nombrado):
        command.upgrade(config_alembic, "head")

    assert _version(base) == ANTERIOR
    fila = dict(zip(("formato", "plataforma"), _leer(base)[id_]))
    assert {campo: fila[campo] for campo in columnas} == columnas


def test_la_migracion_se_deshace_sin_perder_nada(base, config_alembic):
    esperado = {
        _insertar(base, formato="short", plataforma=["instagram"]): ("reel", "instagram"),
        _insertar(base, formato="video_largo", plataforma=["youtube"]): ("video", "youtube"),
        _insertar(base, formato="post_individual", plataforma=[]): ("post", None),
        _insertar(base, formato="carrusel", plataforma=["tiktok"]): ("carrusel", "tiktok"),
    }

    command.downgrade(config_alembic, ANTERIOR)

    assert _leer(base) == esperado


@pytest.mark.parametrize(
    "columnas", [{"formato": "poster"}, {"plataforma": ["instagram", "tiktok"]}]
)
def test_lo_que_la_version_anterior_no_sabe_guardar_detiene_la_vuelta(
    base, config_alembic, columnas: dict
):
    """Un póster no tiene formato viejo, y la plataforma vieja guarda un solo
    destino. La parada nombra la pieza.
    """
    id_ = _insertar(base, **columnas)

    with pytest.raises(RuntimeError, match=rf"\b{id_}\b"):
        command.downgrade(config_alembic, ANTERIOR)

    assert _version(base) == ScriptDirectory.from_config(config_alembic).get_current_head()
