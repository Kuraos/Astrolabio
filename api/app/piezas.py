"""Piezas y su autorización (criterios C1–C5).

El §2.3 no admite matices: cada endpoint comprueba el rol **en el servidor**.
Que la aplicación viva en una red privada no cambia nada — los dos roles del
§1 necesitan identidad para funcionar, y el historial de quién hizo qué es la
mitad del valor del producto.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .db import get_db
from .models import Pieza, Usuario

router = APIRouter(prefix="/api/piezas", tags=["piezas"])


class PiezaNueva(BaseModel):
    titulo: str


class PiezaPublica(BaseModel):
    """Sin campo `estado`, como el modelo: §2.8 sigue vigente."""

    model_config = {"from_attributes": True}

    id: int
    titulo: str
    creada_en: datetime
    creada_por: str


@router.get("", response_model=list[PiezaPublica])
def listar_piezas(
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> list[Pieza]:
    """C3: los dos roles ven la misma lista.

    La sesión se exige igual aunque no se use el usuario: sin ella esto sería
    un endpoint público, y C5 pide 401 en todo salvo `health` y `login`.
    """
    return db.query(Pieza).order_by(Pieza.creada_en.desc()).all()


@router.post("", response_model=PiezaPublica, status_code=status.HTTP_201_CREATED)
def crear_pieza(
    nueva: PiezaNueva,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Pieza:
    """C2: solo `investigador`.

    403 y no otra cosa: significa «sé quién eres y no puedes». Un 401 diría
    que no se sabe quién es, y un 404 escondería que la ruta existe.
    """
    if usuario.rol != "investigador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    pieza = Pieza(titulo=nueva.titulo, creada_por=usuario.usuario)
    db.add(pieza)
    db.commit()
    db.refresh(pieza)

    return pieza
