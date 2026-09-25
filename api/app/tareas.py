"""Las tareas: la checklist de cada pieza y las sueltas (criterios AD1–AD3).

Los dos roles hacen todo con cualquier tarea, como con el material: no hay
ninguna regla de un solo rol (decisión 5 de la Fase 6). Sin sesión, 401, como
todo lo demás (C5). Quién crea y quién marca sale de la sesión, nunca del
cuerpo (M1).

La checklist informa y no bloquea (decisión 2): ningún traspaso mira las
tareas.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, StringConstraints
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .db import get_db
from .models import Pieza, Tarea, Usuario

router = APIRouter(prefix="/api/tareas", tags=["tareas"])


class TareaNueva(BaseModel):
    """Quién la crea no viene aquí: sale de la sesión."""

    # AD2: vacío o solo espacios, 422.
    texto: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    # Sin pieza, la tarea es suelta (decisión 1).
    pieza_id: int | None = None


class TareaMarcada(BaseModel):
    hecha: bool


class TareaPublica(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    pieza_id: int | None
    texto: str
    hecha: bool
    marcada_por: str | None
    marcada_en: datetime | None
    creada_por: str
    creada_en: datetime


@router.get("", response_model=list[TareaPublica])
def listar_tareas(
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> list[Tarea]:
    """AD2: todas en un pedido, en orden de llegada. El tablero cuenta las de
    cada pieza y la pantalla principal enseña las sueltas.
    """
    return db.query(Tarea).order_by(Tarea.id).all()


@router.post("", response_model=TareaPublica, status_code=status.HTTP_201_CREATED)
def crear_tarea(
    nueva: TareaNueva,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Tarea:
    if nueva.pieza_id is not None and db.get(Pieza, nueva.pieza_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    tarea = Tarea(texto=nueva.texto, pieza_id=nueva.pieza_id, creada_por=usuario.usuario)
    db.add(tarea)
    db.commit()
    db.refresh(tarea)

    return tarea


@router.patch("/{tarea_id}", response_model=TareaPublica)
def marcar_tarea(
    tarea_id: int,
    marca: TareaMarcada,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Tarea:
    """Marcarla guarda quién y cuándo; desmarcarla los borra (AD1).

    Marcar una que ya está hecha no cambia quién la marcó. `FOR UPDATE`, como
    en los traspasos: si los dos la marcan a la vez, el segundo espera, ve la
    marca del primero y la deja.
    """
    tarea = db.get(Tarea, tarea_id, with_for_update=True, populate_existing=True)
    if tarea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if not marca.hecha:
        tarea.marcada_por = None
        tarea.marcada_en = None
    elif not tarea.hecha:
        tarea.marcada_por = usuario.usuario
        # El reloj de la base, el mismo de `creada_en`.
        tarea.marcada_en = func.now()

    db.commit()
    db.refresh(tarea)

    return tarea


@router.delete("/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_tarea(
    tarea_id: int,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> None:
    """No es historia (§2.6), como el material: quitarla la borra."""
    tarea = db.get(Tarea, tarea_id)
    if tarea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    db.delete(tarea)
    db.commit()
