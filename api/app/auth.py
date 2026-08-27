"""Autenticación (criterios B2–B5).

Sesión con estado en Postgres, según el ADR 0006: la cookie lleva un testigo
opaco y la fila manda. Por eso `logout` invalida de verdad.
"""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import Sesion, Usuario
from .security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "astrolabio_sesion"
DURACION = timedelta(days=7)

# Coste de referencia para gastar el mismo tiempo cuando el usuario no existe
# (B3). Se calcula una vez al importar, con los mismos parámetros que los
# hashes reales, porque es su coste el que hay que imitar.
_HASH_SENUELO = hash_password(secrets.token_urlsafe(16))

# Mensaje único: cualquier diferencia entre «no existe» y «clave incorrecta»
# convierte el endpoint en un oráculo de qué cuentas hay.
_CREDENCIALES_INVALIDAS = "Usuario o contraseña incorrectos"


class Credenciales(BaseModel):
    usuario: str
    password: str


class UsuarioPublico(BaseModel):
    """Lo único que sale de la API sobre un usuario.

    Es un `response_model`, no un diccionario armado a mano: FastAPI descarta
    todo lo que no esté declarado aquí, así que el hash no puede escaparse ni
    aunque alguien devuelva el objeto entero por descuido (B4).
    """

    usuario: str
    rol: str


@router.post("/login", response_model=UsuarioPublico)
def login(
    credenciales: Credenciales,
    response: Response,
    db: Session = Depends(get_db),
) -> Usuario:
    usuario = db.query(Usuario).filter_by(usuario=credenciales.usuario).one_or_none()

    # Se verifica siempre, exista o no: contra el señuelo si no existe. Sin
    # esto, la respuesta para un usuario inexistente vuelve en microsegundos
    # y la de uno real tarda decenas de milisegundos — diferencia medible
    # desde fuera, y es justo lo que B3 prohíbe.
    almacenado = usuario.hash_password if usuario else _HASH_SENUELO
    correcta = verify_password(almacenado, credenciales.password)

    if usuario is None or not correcta:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=_CREDENCIALES_INVALIDAS
        )

    sesion = Sesion(
        # El testigo *es* la credencial: aleatoriedad criptográfica, no uuid4,
        # que no está diseñado para ser impredecible.
        id=secrets.token_urlsafe(32),
        usuario_id=usuario.id,
        expira_en=datetime.now(UTC) + DURACION,
    )
    db.add(sesion)
    db.commit()

    response.set_cookie(
        key=COOKIE_NAME,
        value=sesion.id,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
        max_age=int(DURACION.total_seconds()),
    )

    return usuario


def usuario_actual(
    astrolabio_sesion: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia de autenticación.

    Es la puerta que usará toda la Fase C: la autorización se comprueba en el
    servidor, siempre (§2.3), y empieza por saber quién pregunta.
    """
    if astrolabio_sesion is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    sesion = db.get(Sesion, astrolabio_sesion)

    if sesion is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if sesion.expira_en < datetime.now(UTC):
        # Caducada es lo mismo que inexistente, y se limpia de paso.
        db.delete(sesion)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return sesion.usuario


@router.get("/me", response_model=UsuarioPublico)
def me(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    return usuario


@router.post("/logout")
def logout(
    response: Response,
    _: Usuario = Depends(usuario_actual),
    astrolabio_sesion: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Borra la fila, no solo la cookie.

    Si solo se borrara la cookie, quien tuviera copia del testigo seguiría
    dentro y B5 no se cumpliría.

    Exige sesión aunque parezca innecesario —cerrar sesión sin tenerla podría
    devolver 200 tranquilamente— porque C5 dice «401 en todo salvo `health` y
    `login`», y `logout` no está en esa lista.
    """
    if astrolabio_sesion is not None:
        sesion = db.get(Sesion, astrolabio_sesion)
        if sesion is not None:
            db.delete(sesion)
            db.commit()

    response.delete_cookie(COOKIE_NAME, path="/")
    return {"cerrada": True}
