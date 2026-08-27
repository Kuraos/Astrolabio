"""Criterio B1 — la siembra crea un `investigador` y un `editor`."""

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Usuario
from app.security import verify_password
from app.seed import Semilla, sembrar_usuarios, semillas_del_entorno

SEMILLAS = [
    Semilla(usuario="johan", password="clave-investigador", rol="investigador"),
    Semilla(usuario="dathzon", password="clave-editor", rol="editor"),
]


def test_la_siembra_crea_los_dos_roles(sesion_db: Session):
    sembrar_usuarios(sesion_db, SEMILLAS)

    roles = {u.usuario: u.rol for u in sesion_db.query(Usuario).all()}

    assert roles == {"johan": "investigador", "dathzon": "editor"}


def test_la_siembra_no_guarda_la_contrasena_en_claro(sesion_db: Session):
    """Lo que B4 protege. Un fallo aquí no se ve por pantalla: la aplicación
    funciona idéntica con las contraseñas en claro hasta que se filtra la base.
    """
    sembrar_usuarios(sesion_db, SEMILLAS)

    guardado = sesion_db.query(Usuario).filter_by(usuario="johan").one()

    assert guardado.hash_password != "clave-investigador"
    assert verify_password(guardado.hash_password, "clave-investigador") is True


def test_las_semillas_salen_de_la_configuracion():
    """B1 pide contraseñas «leídas del entorno». La configuración entra como
    argumento en vez de leerse de un singleton: así la prueba no tiene que
    manipular variables de entorno del proceso para comprobar el mapeo.
    """
    config = Settings(
        database_url="postgresql+psycopg://irrelevante/para-esta-prueba",
        seed_investigador_user="johan",
        seed_investigador_password="clave-uno",
        seed_editor_user="dathzon",
        seed_editor_password="clave-dos",
    )

    semillas = semillas_del_entorno(config)

    assert [(s.usuario, s.rol, s.password) for s in semillas] == [
        ("johan", "investigador", "clave-uno"),
        ("dathzon", "editor", "clave-dos"),
    ]


def test_sembrar_dos_veces_no_duplica_ni_revienta(sesion_db: Session):
    """El script se ejecuta en cada arranque del entorno de quien programa.
    Si la segunda vez explota contra la restricción de unicidad, deja de ser
    utilizable y se termina sembrando a mano.
    """
    sembrar_usuarios(sesion_db, SEMILLAS)
    sembrar_usuarios(sesion_db, SEMILLAS)

    assert sesion_db.query(Usuario).count() == 2
