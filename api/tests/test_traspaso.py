"""Criterios L1–L5 y M1–M2 — la pieza cambia de manos, y la historia lo recuerda.

Las pruebas de L le pegan directamente a la API con la cookie de cada rol, como
las de C: ocultar un botón no es autorización (§2.3). Las reglas se escriben
aquí de nuevo, copiadas del §3 de `docs/estados-del-flujo.md`, y no se importan
de `traspasos.py`: si el código y el documento se separan, estas pruebas son
las que se enteran.

Las de M2 no comprueban que el código evite el `UPDATE`: lo ejecutan por SQL,
como lo haría un script de corrección o una sesión de `psql`, y esperan que la
base lo rechace (ADR 0008). Así fallan también si una migración retira el
trigger.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app import main
from app.db import get_db
from app.models import Pieza, Traspaso
from app.seed import Semilla, sembrar_usuarios

CLAVE = "clave-de-prueba"

# Las de un solo rol: transición, desde, hacia, quién puede y quién no.
SOLO_UN_ROL = [
    ("entregar", "investigacion", "solicitud_entregada", "johan", "dathzon"),
    ("devolver", "solicitud_entregada", "investigacion", "dathzon", "johan"),
    ("finalizar", "material_aprobado", "finalizada", "dathzon", "johan"),
    ("devolver", "finalizada", "material_aprobado", "johan", "dathzon"),
    ("aprobar_diseno", "finalizada", "diseno_aprobado", "johan", "dathzon"),
    ("publicar", "diseno_aprobado", "publicada", "johan", "dathzon"),
]

# Las que puede dar cualquiera de los dos: transición, desde, hacia.
DE_CUALQUIERA = [
    ("aprobar_material", "solicitud_entregada", "material_aprobado"),
    ("reformular", "solicitud_entregada", "investigacion"),
    ("reformular", "material_aprobado", "investigacion"),
    ("reformular", "finalizada", "investigacion"),
    ("reformular", "diseno_aprobado", "investigacion"),
]


def _ids(casos: list[tuple]) -> list[str]:
    return [f"{transicion}-desde-{desde}" for transicion, desde, *_ in casos]


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
    respuesta = cliente.post(
        "/api/auth/login", json={"usuario": usuario, "password": CLAVE}
    )
    assert respuesta.status_code == 200, "la prueba necesita una sesión válida"


def _pieza_en(sesion_db: Session, estado: str) -> Pieza:
    """La pieza se pone directamente en el estado de partida: cada prueba mira
    una regla, no el camino para llegar a ella.
    """
    pieza = Pieza(titulo="Las Pléyades", creada_por="johan", estado=estado)
    sesion_db.add(pieza)
    sesion_db.flush()
    return pieza


def _mover(cliente: TestClient, pieza: Pieza, transicion: str, desde: str, **extra):
    return cliente.post(
        f"/api/piezas/{pieza.id}/traspasos",
        json={"transicion": transicion, "desde": desde, **extra},
    )


def _historia(sesion_db: Session, pieza: Pieza) -> list[Traspaso]:
    return sesion_db.query(Traspaso).filter_by(pieza_id=pieza.id).all()


# --- L1 y L5 ---


@pytest.mark.parametrize(
    "transicion, desde, hacia, quien_puede",
    [caso[:4] for caso in SOLO_UN_ROL],
    ids=_ids(SOLO_UN_ROL),
)
def test_quien_puede_mueve_la_pieza_y_queda_en_la_historia(
    cliente: TestClient,
    sesion_db: Session,
    transicion: str,
    desde: str,
    hacia: str,
    quien_puede: str,
):
    """L5 de paso: el estado y su fila de historia cambian juntos."""
    pieza = _pieza_en(sesion_db, desde)
    _entrar_como(cliente, quien_puede)

    respuesta = _mover(cliente, pieza, transicion, desde)

    assert respuesta.status_code == 201, respuesta.text
    sesion_db.refresh(pieza)
    assert pieza.estado == hacia
    [fila] = _historia(sesion_db, pieza)
    assert (fila.transicion, fila.desde, fila.hacia, fila.creado_por) == (
        transicion,
        desde,
        hacia,
        quien_puede,
    )


# --- L2 ---


@pytest.mark.parametrize(
    "transicion, desde, quien_no",
    [(transicion, desde, quien_no) for transicion, desde, _, _, quien_no in SOLO_UN_ROL],
    ids=_ids(SOLO_UN_ROL),
)
def test_cada_regla_de_un_solo_rol_le_da_403_al_otro(
    cliente: TestClient, sesion_db: Session, transicion: str, desde: str, quien_no: str
):
    """Seis pruebas, una por regla. Y como en C2, un 403 no deja rastro: ni
    cambia el estado ni escribe historia.
    """
    pieza = _pieza_en(sesion_db, desde)
    _entrar_como(cliente, quien_no)

    respuesta = _mover(cliente, pieza, transicion, desde)

    assert respuesta.status_code == 403
    sesion_db.refresh(pieza)
    assert pieza.estado == desde
    assert _historia(sesion_db, pieza) == []


# --- L3 ---


@pytest.mark.parametrize("usuario", ["johan", "dathzon"])
@pytest.mark.parametrize(
    "transicion, desde, hacia", DE_CUALQUIERA, ids=_ids(DE_CUALQUIERA)
)
def test_las_de_cualquiera_las_dan_los_dos(
    cliente: TestClient,
    sesion_db: Session,
    transicion: str,
    desde: str,
    hacia: str,
    usuario: str,
):
    pieza = _pieza_en(sesion_db, desde)
    _entrar_como(cliente, usuario)

    respuesta = _mover(cliente, pieza, transicion, desde)

    assert respuesta.status_code == 201, respuesta.text
    sesion_db.refresh(pieza)
    assert pieza.estado == hacia


# --- L4 ---


@pytest.mark.parametrize(
    "transicion, desde",
    [
        ("publicar", "finalizada"),
        ("reformular", "investigacion"),
        ("reformular", "publicada"),
        ("entregar", "publicada"),
    ],
    ids=[
        "saltarse-la-aprobacion-del-diseno",
        "reformular-lo-que-empieza",
        "reformular-lo-publicado",
        "nada-sale-de-publicada",
    ],
)
def test_una_transicion_que_no_sale_de_ese_estado_es_409(
    cliente: TestClient, sesion_db: Session, transicion: str, desde: str
):
    pieza = _pieza_en(sesion_db, desde)
    _entrar_como(cliente, "johan")

    respuesta = _mover(cliente, pieza, transicion, desde)

    assert respuesta.status_code == 409
    sesion_db.refresh(pieza)
    assert pieza.estado == desde
    assert _historia(sesion_db, pieza) == []


def test_dos_personas_aprueban_el_material_a_la_vez(
    cliente: TestClient, sesion_db: Session
):
    """La pantalla vieja. Los dos ven la solicitud entregada y los dos pulsan
    «aprobar el material»; el segundo llega cuando la pieza ya no está ahí.

    Es la misma comprobación que cierra la carrera real, donde además el
    `FOR UPDATE` hace esperar al segundo hasta que el primero termina.
    """
    pieza = _pieza_en(sesion_db, "solicitud_entregada")

    _entrar_como(cliente, "dathzon")
    primera = _mover(cliente, pieza, "aprobar_material", "solicitud_entregada")
    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "johan")
    segunda = _mover(cliente, pieza, "aprobar_material", "solicitud_entregada")

    assert primera.status_code == 201
    assert segunda.status_code == 409
    assert len(_historia(sesion_db, pieza)) == 1


def test_mover_una_pieza_que_no_existe_es_404(cliente: TestClient):
    _entrar_como(cliente, "johan")

    respuesta = cliente.post(
        "/api/piezas/999999/traspasos",
        json={"transicion": "entregar", "desde": "investigacion"},
    )

    assert respuesta.status_code == 404


# --- M1 ---


def test_quien_sale_de_la_sesion_y_no_del_cuerpo(
    cliente: TestClient, sesion_db: Session
):
    """Como `creada_por`: si lo mandara el cliente, cualquiera podría
    atribuirle un traspaso al otro.
    """
    pieza = _pieza_en(sesion_db, "investigacion")
    _entrar_como(cliente, "johan")

    respuesta = _mover(
        cliente, pieza, "entregar", "investigacion", creado_por="dathzon"
    )

    assert respuesta.json()["creado_por"] == "johan"


def test_devolver_lleva_la_nota_de_que_ajustar(
    cliente: TestClient, sesion_db: Session
):
    """La nota existe para esto: sin ella, cada devolución termina en un
    mensaje de «¿qué ajusto?».
    """
    pieza = _pieza_en(sesion_db, "finalizada")
    _entrar_como(cliente, "johan")
    nota = "El título no cabe en el formato vertical."

    respuesta = _mover(cliente, pieza, "devolver", "finalizada", nota=nota)

    assert respuesta.status_code == 201
    [fila] = _historia(sesion_db, pieza)
    assert fila.nota == nota


# --- M3 ---


def test_los_dos_leen_la_historia_entera_en_orden(
    cliente: TestClient, sesion_db: Session
):
    pieza = _pieza_en(sesion_db, "investigacion")
    _entrar_como(cliente, "johan")
    assert _mover(cliente, pieza, "entregar", "investigacion").status_code == 201
    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "dathzon")
    pasos = [
        ("aprobar_material", "solicitud_entregada"),
        ("finalizar", "material_aprobado"),
    ]
    for transicion, desde in pasos:
        assert _mover(cliente, pieza, transicion, desde).status_code == 201

    como_editor = cliente.get(f"/api/piezas/{pieza.id}/traspasos")
    cliente.post("/api/auth/logout")
    _entrar_como(cliente, "johan")
    como_investigador = cliente.get(f"/api/piezas/{pieza.id}/traspasos")

    assert como_editor.status_code == 200
    assert como_editor.json() == como_investigador.json()
    assert [(t["transicion"], t["creado_por"]) for t in como_editor.json()] == [
        ("entregar", "johan"),
        ("aprobar_material", "dathzon"),
        ("finalizar", "dathzon"),
    ]


def test_la_historia_de_una_pieza_que_no_existe_es_404(cliente: TestClient):
    _entrar_como(cliente, "johan")

    assert cliente.get("/api/piezas/999999/traspasos").status_code == 404


# --- M2 ---


def _un_traspaso(sesion_db: Session) -> Traspaso:
    pieza = _pieza_en(sesion_db, "solicitud_entregada")
    traspaso = Traspaso(
        pieza_id=pieza.id,
        transicion="entregar",
        desde="investigacion",
        hacia="solicitud_entregada",
        creado_por="johan",
    )
    sesion_db.add(traspaso)
    sesion_db.flush()
    return traspaso


def test_la_historia_crece(sesion_db: Session):
    """Append-only es la mitad de la regla: insertar sí se puede."""
    primero = _un_traspaso(sesion_db)
    sesion_db.add(
        Traspaso(
            pieza_id=primero.pieza_id,
            transicion="devolver",
            desde="solicitud_entregada",
            hacia="investigacion",
            creado_por="dathzon",
            nota="Hay dos errores de ortografía en el copy.",
        )
    )
    sesion_db.flush()

    historia = sesion_db.query(Traspaso).filter_by(pieza_id=primero.pieza_id)
    assert historia.count() == 2


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE traspaso SET nota = 'reescrita' WHERE id = {id}",
        "DELETE FROM traspaso WHERE id = {id}",
        "TRUNCATE traspaso",
    ],
    ids=["update", "delete", "truncate"],
)
def test_la_base_no_deja_reescribir_la_historia(sesion_db: Session, sentencia: str):
    """`TRUNCATE` también: es un borrado sin `WHERE`, y un trigger por fila no
    lo vería.
    """
    traspaso = _un_traspaso(sesion_db)

    with pytest.raises(DBAPIError, match="append-only"):
        sesion_db.execute(text(sentencia.format(id=traspaso.id)))
