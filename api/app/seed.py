"""Siembra inicial (criterio B1).

Crea los dos usuarios del §1 —un `investigador` y un `editor`— con las
contraseñas leídas del entorno.

Es idempotente a propósito: se ejecuta en cada arranque del entorno de quien
programa, y un script que revienta la segunda vez acaba sustituido por
`INSERT`s escritos a mano en una terminal.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .config import Settings
from .models import Usuario
from .security import hash_password


@dataclass(frozen=True)
class Semilla:
    usuario: str
    password: str
    rol: str


def semillas_del_entorno(config: Settings) -> list[Semilla]:
    """Traduce la configuración a semillas.

    La configuración entra como argumento en vez de leerse de un singleton
    del módulo: así `sembrar_usuarios` no depende del entorno del proceso y
    la prueba no tiene que manipularlo para comprobar el mapeo.
    """
    return [
        Semilla(
            usuario=config.seed_investigador_user,
            password=config.seed_investigador_password,
            rol="investigador",
        ),
        Semilla(
            usuario=config.seed_editor_user,
            password=config.seed_editor_password,
            rol="editor",
        ),
    ]


def sembrar_usuarios(session: Session, semillas: list[Semilla]) -> int:
    """Inserta los que falten y deja intactos los que ya están.

    No actualiza la contraseña de un usuario existente: si alguien la cambió,
    la siembra no es quién para revertirla.
    """
    creados = 0

    for semilla in semillas:
        existe = (
            session.query(Usuario).filter_by(usuario=semilla.usuario).one_or_none()
        )
        if existe is not None:
            continue

        session.add(
            Usuario(
                usuario=semilla.usuario,
                hash_password=hash_password(semilla.password),
                rol=semilla.rol,
            )
        )
        creados += 1

    session.flush()
    return creados
