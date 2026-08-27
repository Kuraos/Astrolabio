"""Sonda de cookie para el criterio A4.

Esto no es funcionalidad, es un instrumento de medición. El brief §5.3 manda
probar Tailscale **antes** de la autenticación: si una cookie no sobrevive el
viaje por la red privada, cambia el diseño de sesión, y sale mucho más barato
descubrirlo con cero código de auth escrito que con el login ya montado.

Para que la medición signifique algo, la cookie se emite con **exactamente**
los atributos que llevará la sesión real (`HttpOnly`, `SameSite=Lax`, `Secure`
según el entorno). Una sonda con atributos más permisivos que la sesión daría
un falso positivo, que es peor que no medir.

Este módulo entero se borra cuando aterrice la Fase B.
"""

import secrets

from fastapi import APIRouter, Request, Response

from .config import settings

router = APIRouter(prefix="/api/_probe", tags=["sonda"])

COOKIE_NAME = "astrolabio_probe"


@router.post("/cookie")
def set_probe_cookie(response: Response) -> dict:
    """Emite la cookie y devuelve el testigo que acaba de escribir."""
    token = secrets.token_urlsafe(16)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/",
    )

    return {"issued": token}


@router.get("/cookie")
def read_probe_cookie(request: Request) -> dict:
    """Informa si el navegador devolvió la cookie en esta petición.

    Es la mitad que importa: que el servidor sepa emitirla no prueba nada;
    lo que se mide es si el navegador la guardó y la reenvió.
    """
    value = request.cookies.get(COOKIE_NAME)

    return {"present": value is not None, "value": value}


@router.delete("/cookie")
def clear_probe_cookie(response: Response) -> dict:
    """Permite repetir la prueba desde cero sin hurgar en el navegador."""
    response.delete_cookie(COOKIE_NAME, path="/")

    return {"cleared": True}
