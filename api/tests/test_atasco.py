"""Criterios AX1–AX5 — dónde se atasca cada pieza (Fase 10).

La cuenta se prueba sobre historias armadas a mano, sin base: es una función
pura, y las marcas de tiempo de una prueba con base serían todas iguales
—`now()` es la hora en que empezó la transacción, y cada prueba corre en una—.
El endpoint se prueba aparte, con las marcas escritas a mano.

El 401 sin sesión lo cubre la prueba de C5, que recorre el esquema OpenAPI.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import main
from app.atasco import tiempos
from app.db import get_db
from app.models import Pieza, Traspaso
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"
CREADA = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
DIA = timedelta(days=1)
HORA = timedelta(hours=1)


def _paso(transicion: str, hacia: str, cuando: datetime) -> Traspaso:
    return Traspaso(transicion=transicion, hacia=hacia, creado_en=cuando)


def _etapas(resultado) -> dict[str, timedelta]:
    return {estado: timedelta(seconds=s) for estado, s in resultado.etapas.items()}


# El recorrido entero, sin vueltas: 3 días de investigación, 1 de solicitud,
# 4 de diseño en manos del editor, 2 de revisión y 1 hasta publicarla.
PUBLICADA = [
    _paso("entregar", "solicitud_entregada", CREADA + 3 * DIA),
    _paso("aprobar_material", "material_aprobado", CREADA + 4 * DIA),
    _paso("finalizar", "finalizada", CREADA + 8 * DIA),
    _paso("aprobar_diseno", "diseno_aprobado", CREADA + 10 * DIA),
    _paso("publicar", "publicada", CREADA + 11 * DIA),
]

# Entregada, devuelta, entregada otra vez, y ahí sigue: en curso.
DEVUELTA = [
    _paso("entregar", "solicitud_entregada", CREADA + 2 * DIA),
    _paso("devolver", "investigacion", CREADA + 3 * DIA),
    _paso("entregar", "solicitud_entregada", CREADA + 6 * DIA),
]


# --- AX2 ---


def test_una_pieza_sin_traspasos_lleva_en_investigacion_desde_que_nacio():
    ahora = CREADA + 5 * DIA

    resultado = tiempos(CREADA, [], ahora)

    assert _etapas(resultado) == {"investigacion": 5 * DIA}
    assert resultado.en_estado == (5 * DIA).total_seconds()


def test_cada_estado_cuenta_de_un_traspaso_al_siguiente():
    resultado = tiempos(CREADA, PUBLICADA, CREADA + 30 * DIA)

    assert _etapas(resultado) == {
        "investigacion": 3 * DIA,
        "solicitud_entregada": 1 * DIA,
        "material_aprobado": 4 * DIA,
        "finalizada": 2 * DIA,
        "diseno_aprobado": 1 * DIA,
    }


def test_publicarla_cierra_la_cuenta():
    """De `publicada` no sale nada: el tiempo después no es de ninguna etapa, y
    la pieza ya no «lleva» días en ningún sitio.
    """
    antes = tiempos(CREADA, PUBLICADA, CREADA + 12 * DIA)
    mucho_despues = tiempos(CREADA, PUBLICADA, CREADA + 400 * DIA)

    assert antes == mucho_despues
    assert "publicada" not in antes.etapas
    assert antes.en_estado is None


def test_la_pieza_en_curso_suma_hasta_ahora_en_su_estado():
    ahora = CREADA + 6 * DIA + 5 * HORA

    resultado = tiempos(CREADA, DEVUELTA, ahora)

    assert resultado.en_estado == (5 * HORA).total_seconds()


# --- AX3 ---


def test_volver_a_un_estado_suma_su_tiempo_y_la_devolucion_se_cuenta():
    resultado = tiempos(CREADA, DEVUELTA, CREADA + 7 * DIA)

    # 2 días antes de entregarla y 3 después de que se la devolvieran.
    assert _etapas(resultado) == {
        "investigacion": 5 * DIA,
        "solicitud_entregada": 2 * DIA,
    }
    # La estancia de ahora, no las dos: lleva un día donde está.
    assert resultado.en_estado == DIA.total_seconds()
    assert (resultado.devoluciones, resultado.reformulaciones) == (1, 0)


def test_reformular_se_cuenta_aparte_de_devolver():
    historia = [
        _paso("entregar", "solicitud_entregada", CREADA + DIA),
        _paso("aprobar_material", "material_aprobado", CREADA + 2 * DIA),
        _paso("reformular", "investigacion", CREADA + 3 * DIA),
    ]

    resultado = tiempos(CREADA, historia, CREADA + 4 * DIA)

    assert (resultado.devoluciones, resultado.reformulaciones) == (0, 1)
    assert _etapas(resultado)["investigacion"] == 2 * DIA


@pytest.mark.parametrize(
    "historia, fin",
    [
        ([], CREADA + 9 * DIA),
        (PUBLICADA, CREADA + 11 * DIA),
        (DEVUELTA, CREADA + 9 * DIA),
    ],
    ids=["sin-traspasos", "publicada", "devuelta"],
)
def test_la_suma_de_las_etapas_es_la_vida_de_la_pieza(historia, fin):
    """Hasta ahora, o hasta la publicación si ya salió."""
    resultado = tiempos(CREADA, historia, CREADA + 9 * DIA)

    assert sum(resultado.etapas.values()) == (fin - CREADA).total_seconds()


# --- AX4 ---


def test_ninguna_duracion_sale_negativa_con_marcas_invertidas():
    """`creado_en` es la hora en que empezó cada transacción: el segundo de dos
    traspasos seguidos puede llevar una marca anterior al primero. La historia
    se ordena por `id`, no por hora (M3), y la cuenta tiene que aguantarlo sin
    restar ni inventar tiempo.
    """
    historia = [
        _paso("entregar", "solicitud_entregada", CREADA + DIA),
        # Aprobado 300 ms «antes» de que se entregara.
        _paso(
            "aprobar_material",
            "material_aprobado",
            CREADA + DIA - timedelta(milliseconds=300),
        ),
    ]
    ahora = CREADA + 3 * DIA

    resultado = tiempos(CREADA, historia, ahora)

    assert all(segundos >= 0 for segundos in resultado.etapas.values())
    assert resultado.etapas["solicitud_entregada"] == 0
    assert _etapas(resultado)["material_aprobado"] == 2 * DIA
    # Sin el tiempo inventado que saldría de contar desde la marca anterior.
    assert sum(resultado.etapas.values()) == (ahora - CREADA).total_seconds()


def test_un_ahora_anterior_al_ultimo_traspaso_no_da_tiempo_negativo():
    historia = [_paso("entregar", "solicitud_entregada", CREADA + DIA)]

    resultado = tiempos(CREADA, historia, CREADA + DIA - HORA)

    assert resultado.en_estado == 0
    assert all(segundos >= 0 for segundos in resultado.etapas.values())


# --- AX5 ---


def test_el_ciclo_va_de_la_primera_entrega_a_la_publicacion():
    resultado = tiempos(CREADA, PUBLICADA, CREADA + 30 * DIA)

    assert resultado.ciclo == (8 * DIA).total_seconds()


def test_el_ciclo_cuenta_desde_la_primera_entrega_aunque_la_devolvieran():
    resultado = tiempos(CREADA, DEVUELTA, CREADA + 10 * DIA)

    # Abierto: de la primera entrega, el día 2, hasta ahora.
    assert resultado.ciclo == (8 * DIA).total_seconds()


def test_sin_entregar_no_hay_ciclo():
    assert tiempos(CREADA, [], CREADA + DIA).ciclo is None


# --- AX1 ---


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


@pytest.mark.parametrize("usuario", ["johan", "dathzon"])
def test_los_dos_roles_ven_el_atasco_de_cada_pieza(
    cliente: TestClient, sesion_db: Session, usuario: str
):
    """Con las marcas escritas a mano: en la base de pruebas, `now()` daría la
    misma a todas.
    """
    publicada = Pieza(titulo="M31", creada_por="johan", estado="publicada", creada_en=CREADA)
    nueva = Pieza(titulo="Ío", creada_por="johan")
    sesion_db.add_all([publicada, nueva])
    sesion_db.flush()
    for paso in PUBLICADA:
        sesion_db.add(
            Traspaso(
                pieza_id=publicada.id,
                transicion=paso.transicion,
                desde="da-igual",
                hacia=paso.hacia,
                creado_por="johan",
                creado_en=paso.creado_en,
            )
        )
    sesion_db.flush()
    cliente.post("/api/auth/login", json={"usuario": usuario, "password": CLAVE})

    respuesta = cliente.get("/api/atasco")

    assert respuesta.status_code == 200, respuesta.text
    por_pieza = {fila["pieza_id"]: fila for fila in respuesta.json()}
    assert por_pieza[publicada.id] == {
        "pieza_id": publicada.id,
        # En el orden del flujo, para que el cliente no tenga que ordenarlas.
        "etapas": [
            {"estado": "investigacion", "segundos": (3 * DIA).total_seconds()},
            {"estado": "solicitud_entregada", "segundos": DIA.total_seconds()},
            {"estado": "material_aprobado", "segundos": (4 * DIA).total_seconds()},
            {"estado": "finalizada", "segundos": (2 * DIA).total_seconds()},
            {"estado": "diseno_aprobado", "segundos": DIA.total_seconds()},
        ],
        "en_estado": None,
        "ciclo": (8 * DIA).total_seconds(),
        "devoluciones": 0,
        "reformulaciones": 0,
    }
    # La recién creada lleva en investigación lo que haya pasado desde que
    # empezó la transacción de la prueba: poco, pero no negativo.
    assert por_pieza[nueva.id]["en_estado"] >= 0
    assert [e["estado"] for e in por_pieza[nueva.id]["etapas"]] == ["investigacion"]
    assert por_pieza[nueva.id]["ciclo"] is None
