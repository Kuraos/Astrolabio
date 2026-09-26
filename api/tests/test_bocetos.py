"""Criterios AS–AU de la Fase 9 — los bocetos con Claude (ADR 0016).

Claude se simula: sin red, sin clave y sin gastar. Lo que se prueba es lo que
es de Astrolabio —qué sale, qué se valida, qué se guarda y qué se responde—, y
la forma de la petición al SDK, con un cliente de mentira que la anota. La
llamada real la prueba Johan con su clave (fase 9, §5).
"""

import json
from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import bocetos, main
from app.db import get_db
from app.models import Boceto, Pieza
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

GUION = "La luz del Sol tarda unos 8 minutos en llegar: $t = d/c \\approx 499\\,\\mathrm{s}$."
COPY = [
    "La luz del Sol que ves salió hace 8 minutos",
    "Recorre $d \\approx 1{,}496 \\times 10^{11}\\,\\mathrm{m}$",
]


def _elemento(tipo, peso, contenido, fila, col, filas, cols):
    return {
        "tipo": tipo,
        "peso": peso,
        "contenido": contenido,
        "zona": {"fila": fila, "col": col, "filas": filas, "cols": cols},
    }


def _lamina(numero, *elementos):
    return {
        "numero": numero,
        "idea": f"Lo que comunica la lámina {numero}",
        "elementos": list(elementos),
        "nota_para_la_edicion": "El dato, en grande.",
    }


def _valido():
    """Un boceto que cumple AT1–AT4 para `COPY` en 12 × 15."""
    return {
        "laminas": [
            _lamina(
                1,
                _elemento("titulo", 1, "La luz del Sol que ves salió hace 8 minutos", 2, 2, 4, 10),
                _elemento("figura", 2, "El Sol en ultravioleta", 7, 2, 6, 10),
                _elemento("nota", 4, "Imagen: SDO", 14, 2, 1, 10),
            ),
            _lamina(
                2,
                _elemento("formula", 1, "d \\approx 1{,}496 \\times 10^{11}\\,\\mathrm{m}", 3, 2, 5, 10),
                _elemento("texto", 2, "Recorre", 9, 2, 3, 10),
            ),
        ]
    }


class Claude:
    """Un Claude de mentira: anota lo que se le pide y responde lo que toque."""

    def __init__(self, respuesta=None, fin="end_turn", error=None):
        self.texto = json.dumps(respuesta if respuesta is not None else _valido())
        self.fin = fin
        self.error = error
        self.mensajes: list[str] = []

    def __call__(self, mensaje: str) -> bocetos.Respuesta:
        self.mensajes.append(mensaje)
        if self.error is not None:
            raise self.error
        return bocetos.Respuesta(
            texto=self.texto,
            modelo="claude-opus-5",
            tokens_entrada=2100,
            tokens_salida=2800,
            fin=self.fin,
        )


@pytest.fixture
def claude():
    return Claude()


@pytest.fixture
def cliente(sesion_db: Session, claude: Claude):
    sembrar_usuarios(
        sesion_db,
        [
            Semilla(usuario="johan", password=CLAVE, rol="investigador"),
            Semilla(usuario="dathzon", password=CLAVE, rol="editor"),
        ],
    )
    main.app.dependency_overrides[get_db] = lambda: sesion_db
    main.app.dependency_overrides[bocetos.dibujante] = lambda: claude
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


@pytest.fixture
def pieza(sesion_db: Session) -> Pieza:
    p = Pieza(
        titulo="La luz del Sol tarda 8 minutos",
        creada_por="johan",
        guion=GUION,
        formato="carrusel",
        proposito="educar",
        nivel="basico",
        tema="Sistema Solar",
        plataforma=["instagram", "tiktok"],
        copy_grafico=list(COPY),
        respaldo=["Nota del vault que no sale"],
    )
    sesion_db.add(p)
    sesion_db.flush()
    return p


def _entrar_como(cliente: TestClient, usuario: str = "johan") -> None:
    respuesta = cliente.post("/api/auth/login", json={"usuario": usuario, "password": CLAVE})
    assert respuesta.status_code == 200, "la prueba necesita una sesión válida"


def _pedir(cliente: TestClient, pieza: Pieza):
    return cliente.post(f"/api/piezas/{pieza.id}/bocetos")


def _guardados(sesion_db: Session, pieza: Pieza) -> list[Boceto]:
    return sesion_db.query(Boceto).filter(Boceto.pieza_id == pieza.id).order_by(Boceto.id).all()


# --- AS1: quién pide ---


def test_sin_sesion_es_401(cliente: TestClient, pieza: Pieza):
    assert cliente.get(f"/api/piezas/{pieza.id}/bocetos").status_code == 401
    assert _pedir(cliente, pieza).status_code == 401


@pytest.mark.parametrize("usuario", ["johan", "dathzon"])
def test_los_dos_roles_piden_bocetos(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, usuario: str
):
    """Fase 9, §7.2: el editor es quien los usa. Queda quién lo pidió."""
    _entrar_como(cliente, usuario)

    respuesta = _pedir(cliente, pieza)

    assert respuesta.status_code == 201, respuesta.text
    boceto = respuesta.json()
    assert boceto["creado_por"] == usuario
    assert (boceto["columnas"], boceto["filas"]) == (12, 15)
    assert [lamina["numero"] for lamina in boceto["laminas"]] == [1, 2]
    assert (boceto["tokens_entrada"], boceto["tokens_salida"]) == (2100, 2800)
    assert [b.creado_por for b in _guardados(sesion_db, pieza)] == [usuario]


def test_una_pieza_que_no_existe_da_404(cliente: TestClient):
    _entrar_como(cliente)

    assert cliente.post("/api/piezas/99999/bocetos").status_code == 404


# --- AS2 y AS3: qué sale y cómo se pide ---


def test_sale_el_cuadro_el_copy_y_el_guion_y_nada_mas(
    cliente: TestClient, pieza: Pieza, claude: Claude
):
    _entrar_como(cliente)

    _pedir(cliente, pieza)

    [mensaje] = claude.mensajes
    for esperado in [
        pieza.titulo,
        "Tipo de pieza: carrusel",
        "Destinos: instagram, tiktok",
        "Propósito: educar",
        "Nivel: basico",
        "Tema: Sistema Solar",
        "Rejilla: 12 columnas × 15 filas",
        "### Lámina 2",
        COPY[1],
        GUION,
    ]:
        assert esperado in mensaje
    # Ni el respaldo, que es del vault, ni quién hizo la pieza (§2.5, ADR 0016).
    assert "Nota del vault" not in mensaje
    assert "johan" not in mensaje


def test_la_peticion_pide_la_salida_estructurada():
    """AS3 y AS4, contra un cliente de mentira con la forma del SDK."""
    anotado = {}
    final = SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text='{"laminas": []}'),
        ],
        model="claude-opus-5",
        usage=SimpleNamespace(input_tokens=2100, output_tokens=2800),
        stop_reason="end_turn",
    )

    class Stream:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def get_final_message(self):
            return final

    def stream(**parametros):
        anotado.update(parametros)
        return Stream()

    cliente = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(stream=stream)))

    respuesta = bocetos.pedir_a_claude(cliente, "claude-opus-5", "el mensaje")

    assert anotado["model"] == "claude-opus-5"
    assert anotado["system"] == bocetos.SISTEMA
    assert anotado["messages"] == [{"role": "user", "content": "el mensaje"}]
    assert anotado["output_config"] == {
        "format": {"type": "json_schema", "schema": bocetos.ESQUEMA}
    }
    assert anotado["fallbacks"] == "default"
    assert anotado["betas"] == ["server-side-fallback-2026-07-01"]
    assert respuesta == bocetos.Respuesta(
        texto='{"laminas": []}',
        modelo="claude-opus-5",
        tokens_entrada=2100,
        tokens_salida=2800,
        fin="end_turn",
    )


def test_el_esquema_admite_solo_lo_que_valida_la_app():
    """El esquema sale del modelo con que se valida (AS3): los siete tipos,
    los cuatro pesos y ningún campo de más."""
    definiciones = bocetos.ESQUEMA["$defs"]

    assert definiciones["Elemento"]["properties"]["tipo"]["enum"] == [
        "titulo",
        "dato",
        "texto",
        "formula",
        "figura",
        "grafica",
        "nota",
    ]
    assert definiciones["Elemento"]["properties"]["peso"]["enum"] == [1, 2, 3, 4]
    assert all(d["additionalProperties"] is False for d in definiciones.values())


# --- AS5 y AS6: cuándo no se puede ---


def test_sin_clave_la_app_sigue_y_lo_dice(cliente: TestClient, pieza: Pieza):
    main.app.dependency_overrides[bocetos.dibujante] = lambda: None
    _entrar_como(cliente)

    estado = cliente.get(f"/api/piezas/{pieza.id}/bocetos").json()
    pedido = _pedir(cliente, pieza)

    assert estado["disponible"] is False
    assert "ANTHROPIC_API_KEY" in estado["motivo"]
    assert pedido.status_code == 409
    assert pedido.json()["detail"] == estado["motivo"]


@pytest.mark.parametrize(
    ("cambios", "motivo"),
    [
        ({"formato": None}, "Elige el tipo de pieza"),
        ({"formato": "short"}, "El short y el video largo, más adelante"),
        ({"formato": "video_largo"}, "El short y el video largo, más adelante"),
        ({"copy_grafico": []}, "Escribe y guarda el copy gráfico"),
        ({"copy_grafico": ["", "  "]}, "Escribe y guarda el copy gráfico"),
        ({"formato": "post_individual"}, "Un post individual es una lámina, y el copy gráfico tiene 2"),
        ({"formato": "poster"}, "Un póster es una lámina"),
        ({"copy_grafico": ["x"] * 21}, "20 láminas como mucho"),
    ],
)
def test_lo_que_no_tiene_boceto_es_409_con_su_motivo(
    cliente: TestClient,
    pieza: Pieza,
    sesion_db: Session,
    claude: Claude,
    cambios: dict,
    motivo: str,
):
    for campo, valor in cambios.items():
        setattr(pieza, campo, valor)
    sesion_db.flush()
    _entrar_como(cliente)

    respuesta = _pedir(cliente, pieza)

    assert respuesta.status_code == 409
    assert motivo in respuesta.json()["detail"]
    # Nadie llamó a Claude: no costó nada, y no se guarda.
    assert claude.mensajes == []
    assert _guardados(sesion_db, pieza) == []


# --- AT: la validación ---


def _con(cambio) -> dict:
    boceto = _valido()
    cambio(boceto)
    return boceto


def _pesos_1(boceto):
    boceto["laminas"][0]["elementos"][1]["peso"] = 1


def _sin_peso_1(boceto):
    boceto["laminas"][1]["elementos"][0]["peso"] = 3


def _fuera_por_columnas(boceto):
    boceto["laminas"][0]["elementos"][0]["zona"]["cols"] = 12


def _fuera_por_filas(boceto):
    boceto["laminas"][0]["elementos"][2]["zona"]["filas"] = 3


def _solape(boceto):
    boceto["laminas"][1]["elementos"][1]["zona"]["fila"] = 6


@pytest.mark.parametrize(
    ("boceto", "fallo"),
    [
        (_con(lambda b: b["laminas"].pop()), "trae 1 láminas y el copy tiene 2"),
        (_con(lambda b: b["laminas"][1].update(numero=3)), "la lámina 2 viene numerada 3"),
        (_con(lambda b: b["laminas"][1].update(elementos=[])), "la lámina 2 no tiene elementos"),
        (_con(_pesos_1), "la lámina 1 tiene 2 elementos de peso 1"),
        (_con(_sin_peso_1), "la lámina 2 tiene 0 elementos de peso 1"),
        (_con(_fuera_por_columnas), "en la lámina 1, titulo se sale de la rejilla"),
        (_con(_fuera_por_filas), "en la lámina 1, nota se sale de la rejilla"),
        (_con(_solape), "en la lámina 2, formula y texto se solapan"),
    ],
)
def test_un_boceto_que_no_vale_es_502_y_se_guarda_su_fallo(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, claude: Claude, boceto, fallo
):
    """AT1–AT4 y AT6. El intento costó, así que queda, con sus tokens y sin
    láminas (AU1); y la lista no lo enseña."""
    claude.texto = json.dumps(boceto)
    _entrar_como(cliente)

    respuesta = _pedir(cliente, pieza)

    assert respuesta.status_code == 502
    assert fallo in respuesta.json()["detail"]
    [guardado] = _guardados(sesion_db, pieza)
    assert guardado.laminas is None
    assert fallo in guardado.error
    assert guardado.tokens_salida == 2800
    assert cliente.get(f"/api/piezas/{pieza.id}/bocetos").json()["bocetos"] == []


@pytest.mark.parametrize(
    ("texto", "fin", "fallo"),
    [
        ('{"laminas": [{"numero": 1}]}', "end_turn", "no tiene la forma de un boceto"),
        ("", "max_tokens", "se cortó antes de terminar"),
        ("", "refusal", "Claude declinó"),
    ],
)
def test_una_respuesta_rota_es_502_y_se_guarda(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, claude: Claude, texto, fin, fallo
):
    claude.texto = texto
    claude.fin = fin
    _entrar_como(cliente)

    respuesta = _pedir(cliente, pieza)

    assert respuesta.status_code == 502
    assert fallo in respuesta.json()["detail"]
    assert [b.error is not None for b in _guardados(sesion_db, pieza)] == [True]


def test_el_poster_usa_su_rejilla(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, claude: Claude
):
    """Fase 9, §7.1: 12 × 17. La fila 17 cabe en un póster y no en un 4:5."""
    pieza.formato = "poster"
    pieza.copy_grafico = [COPY[0]]
    sesion_db.flush()
    claude.texto = json.dumps(
        {
            "laminas": [
                _lamina(
                    1,
                    _elemento("titulo", 1, COPY[0], 2, 2, 5, 10),
                    _elemento("nota", 4, "Voz del Cosmos", 17, 2, 1, 10),
                )
            ]
        }
    )
    _entrar_como(cliente)

    respuesta = _pedir(cliente, pieza)

    assert respuesta.status_code == 201, respuesta.text
    assert (respuesta.json()["columnas"], respuesta.json()["filas"]) == (12, 17)
    assert "Rejilla: 12 columnas × 17 filas" in claude.mensajes[0]


# --- AT5: las cifras sin fuente ---


def test_las_cifras_del_guion_y_del_copy_no_avisan(cliente: TestClient, pieza: Pieza):
    """«1{,}496» en el copy y «1,496» en el boceto son la misma cifra."""
    _entrar_como(cliente)

    assert _pedir(cliente, pieza).json()["avisos"] == []


def test_una_cifra_sin_fuente_avisa_y_no_rechaza(
    cliente: TestClient, pieza: Pieza, claude: Claude
):
    boceto = _valido()
    boceto["laminas"][1]["elementos"][1]["contenido"] = "Recorre 150 millones de km en 8 minutos"
    claude.texto = json.dumps(boceto)
    _entrar_como(cliente)

    respuesta = _pedir(cliente, pieza)

    assert respuesta.status_code == 201
    assert respuesta.json()["avisos"] == ["Lámina 2: 150 no está en el guion ni en el copy."]


# --- AS7: lo que falla en Anthropic ---

_PETICION = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def _respuesta_http(codigo: int) -> httpx2.Response:
    return httpx2.Response(codigo, request=_PETICION)


@pytest.mark.parametrize(
    ("error", "detalle"),
    [
        (
            anthropic.AuthenticationError("x", response=_respuesta_http(401), body=None),
            "no acepta la clave",
        ),
        (
            anthropic.RateLimitError("x", response=_respuesta_http(429), body=None),
            "Anthropic pide esperar",
        ),
        (
            anthropic.InternalServerError("x", response=_respuesta_http(500), body=None),
            "La API de Anthropic falló",
        ),
        (anthropic.APIConnectionError(request=_PETICION), "revisa la conexión a internet"),
        (anthropic.APITimeoutError(request=_PETICION), "revisa la conexión a internet"),
    ],
)
def test_un_fallo_de_anthropic_es_502_en_espanol(
    cliente: TestClient, pieza: Pieza, sesion_db: Session, claude: Claude, error, detalle
):
    """No llegó respuesta, así que no hay tokens que guardar."""
    claude.error = error
    _entrar_como(cliente)

    respuesta = _pedir(cliente, pieza)

    assert respuesta.status_code == 502
    assert detalle in respuesta.json()["detail"]
    assert _guardados(sesion_db, pieza) == []


# --- AU2: la lista ---


def test_la_lista_trae_los_validos_del_mas_nuevo_al_mas_viejo(
    cliente: TestClient, pieza: Pieza, claude: Claude
):
    _entrar_como(cliente)
    primero = _pedir(cliente, pieza).json()
    claude.texto = ""
    claude.fin = "max_tokens"
    _pedir(cliente, pieza)
    claude.texto = json.dumps(_valido())
    claude.fin = "end_turn"
    segundo = _pedir(cliente, pieza).json()

    estado = cliente.get(f"/api/piezas/{pieza.id}/bocetos").json()

    assert estado["disponible"] is True
    assert estado["motivo"] is None
    assert [b["id"] for b in estado["bocetos"]] == [segundo["id"], primero["id"]]
    assert estado["bocetos"][0]["copy_grafico"] == COPY
