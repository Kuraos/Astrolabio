"""El material de la pieza (criterios P1–P4 de la Fase 3).

Lo que Johan le pasa al editor para hacer la pieza, y que hoy va por chat. Los
enlaces viven aquí; las imágenes, en la carpeta de la pieza en Syncthing
(ADR 0010), que llega con los criterios Q y R.

Los dos roles añaden y quitan material: es justo lo que se comparte. Sin
sesión, 401, como todo lo demás (C5).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .db import get_db
from .models import Enlace, Pieza, Usuario

router = APIRouter(prefix="/api/piezas", tags=["material"])


class EnlaceNuevo(BaseModel):
    # P3. `HttpUrl` solo admite `http` y `https`: un `javascript:` en un enlace
    # es un XSS esperando el clic, y quien lo impide es el servidor, no el
    # botón que lo pinta (§2.3).
    url: HttpUrl
    nota: str | None = None


class EnlacePublico(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    url: str
    nota: str | None
    creado_por: str
    creado_en: datetime


def _pieza(db: Session, pieza_id: int) -> Pieza:
    pieza = db.get(Pieza, pieza_id)
    if pieza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return pieza


@router.get("/{pieza_id}/enlaces", response_model=list[EnlacePublico])
def enlaces_de_la_pieza(
    pieza_id: int,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> list[Enlace]:
    """P4: en orden de llegada."""
    _pieza(db, pieza_id)
    return db.query(Enlace).filter_by(pieza_id=pieza_id).order_by(Enlace.id).all()


@router.post(
    "/{pieza_id}/enlaces",
    response_model=EnlacePublico,
    status_code=status.HTTP_201_CREATED,
)
def anadir_enlace(
    pieza_id: int,
    nuevo: EnlaceNuevo,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Enlace:
    _pieza(db, pieza_id)

    enlace = Enlace(
        pieza_id=pieza_id,
        url=str(nuevo.url),
        nota=nuevo.nota,
        creado_por=usuario.usuario,
    )
    db.add(enlace)
    db.commit()
    db.refresh(enlace)

    return enlace


@router.delete(
    "/{pieza_id}/enlaces/{enlace_id}", status_code=status.HTTP_204_NO_CONTENT
)
def quitar_enlace(
    pieza_id: int,
    enlace_id: int,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> None:
    """Cualquiera de los dos, igual que lo añade (decisión 6 de la Fase 3).

    El enlace tiene que ser de esa pieza: si no, 404. Una ruta que dijera una
    pieza y borrara el enlace de otra sería un error difícil de ver.
    """
    enlace = db.get(Enlace, enlace_id)
    if enlace is None or enlace.pieza_id != pieza_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    db.delete(enlace)
    db.commit()
