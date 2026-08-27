"""Modelo mínimo de la Fase B: `usuario` y `sesion`.

Se prueba contra Postgres real, no contra SQLite. El §3 eligió Postgres por
motivos concretos —dos personas escribiendo a la vez— y sustituirlo en las
pruebas por otro motor sería probar un sistema distinto del que se despliega.

Cada prueba vive dentro de una transacción externa que se revierte al final,
así que ni un `commit` dentro de la prueba deja rastro en la base.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Sesion, Usuario


def test_un_usuario_se_guarda_con_su_rol(sesion_db: Session):
    sesion_db.add(
        Usuario(usuario="johan", hash_password="$argon2id$fingido", rol="investigador")
    )
    sesion_db.flush()

    guardado = sesion_db.query(Usuario).filter_by(usuario="johan").one()

    assert guardado.rol == "investigador"
    assert guardado.creado_en is not None


def test_el_nombre_de_usuario_no_se_puede_repetir(sesion_db: Session):
    """Sin unicidad, sembrar dos veces crearía un segundo `johan` y el login
    elegiría uno de los dos según el humor del planificador de consultas.
    """
    sesion_db.add(Usuario(usuario="repetido", hash_password="a", rol="editor"))
    sesion_db.flush()

    sesion_db.add(Usuario(usuario="repetido", hash_password="b", rol="editor"))

    with pytest.raises(IntegrityError):
        sesion_db.flush()


def test_una_sesion_apunta_a_su_usuario(sesion_db: Session):
    """El ADR 0006 guarda la sesión como fila, no como cookie firmada: eso es
    lo que permite que `logout` la invalide de verdad.
    """
    usuario = Usuario(usuario="johan", hash_password="x", rol="investigador")
    sesion_db.add(usuario)
    sesion_db.flush()

    sesion_db.add(
        Sesion(
            id="testigo-opaco",
            usuario_id=usuario.id,
            expira_en=datetime.now(UTC) + timedelta(days=7),
        )
    )
    sesion_db.flush()

    guardada = sesion_db.query(Sesion).filter_by(id="testigo-opaco").one()

    assert guardada.usuario.usuario == "johan"
    assert guardada.usuario.rol == "investigador"


def test_borrar_el_usuario_se_lleva_sus_sesiones(sesion_db: Session):
    """Sin cascada quedarían sesiones huérfanas apuntando a un usuario que ya
    no existe, y cada petición con esa cookie sería un 500 en vez de un 401.
    """
    usuario = Usuario(usuario="efimero", hash_password="x", rol="editor")
    sesion_db.add(usuario)
    sesion_db.flush()

    sesion_db.add(
        Sesion(
            id="se-va-con-el",
            usuario_id=usuario.id,
            expira_en=datetime.now(UTC) + timedelta(days=7),
        )
    )
    sesion_db.flush()

    sesion_db.delete(usuario)
    sesion_db.flush()

    assert sesion_db.query(Sesion).filter_by(id="se-va-con-el").one_or_none() is None
