"""Traspasos: la pieza cambia de manos (criterios L1–L5 y M1).

Es el centro del §1. Cada transición es una fila de `TRANSICIONES`, copiada del
§3 de `docs/estados-del-flujo.md`, y la tabla vive aquí y solo aquí: el cliente
preguntará qué puede hacer, no lo deducirá (K4).

El orden de las comprobaciones importa. Primero, si la transición sale de ese
estado (409). Después, si el rol puede darla (403), que no depende de dónde esté
la pieza hoy: el editor no publica nunca, esté donde esté. Por último, si la
pieza sigue donde quien pide cree que está (409).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .db import get_db
from .models import Pieza, Traspaso, Usuario

router = APIRouter(prefix="/api/piezas", tags=["traspasos"])

INVESTIGADOR = frozenset({"investigador"})
EDITOR = frozenset({"editor"})
CUALQUIERA = INVESTIGADOR | EDITOR

# (transición, desde) → (hacia, quién puede darla), con los verbos de sus
# propias frases. Una fila por regla, sin generarlas: añadir un estado tiene que
# obligar a pensar qué sale de él.
TRANSICIONES: dict[tuple[str, str], tuple[str, frozenset[str]]] = {
    ("entregar", "investigacion"): ("solicitud_entregada", INVESTIGADOR),
    ("aprobar_material", "solicitud_entregada"): ("material_aprobado", CUALQUIERA),
    ("devolver", "solicitud_entregada"): ("investigacion", EDITOR),
    ("finalizar", "material_aprobado"): ("finalizada", EDITOR),
    ("devolver", "finalizada"): ("material_aprobado", INVESTIGADOR),
    ("aprobar_diseno", "finalizada"): ("diseno_aprobado", INVESTIGADOR),
    ("publicar", "diseno_aprobado"): ("publicada", INVESTIGADOR),
    # Desde cualquier estado anterior a `publicada`, salvo el propio principio.
    ("reformular", "solicitud_entregada"): ("investigacion", CUALQUIERA),
    ("reformular", "material_aprobado"): ("investigacion", CUALQUIERA),
    ("reformular", "finalizada"): ("investigacion", CUALQUIERA),
    ("reformular", "diseno_aprobado"): ("investigacion", CUALQUIERA),
}


class TraspasoNuevo(BaseModel):
    """Quién lo pide no viene aquí: sale de la sesión (M1)."""

    transicion: str
    # El estado en que quien pide ve la pieza. Si ya no está ahí, 409 (L4).
    desde: str
    nota: str | None = None


class TraspasoPublico(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    transicion: str
    desde: str
    hacia: str
    creado_por: str
    creado_en: datetime
    nota: str | None


@router.post(
    "/{pieza_id}/traspasos",
    response_model=TraspasoPublico,
    status_code=status.HTTP_201_CREATED,
)
def mover_pieza(
    pieza_id: int,
    pedido: TraspasoNuevo,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Traspaso:
    """L1: el único camino por el que una pieza cambia de estado."""
    regla = TRANSICIONES.get((pedido.transicion, pedido.desde))
    if regla is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esa transición no sale de ese estado.",
        )
    hacia, roles = regla

    # L2, antes de mirar la pieza.
    if usuario.rol not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # `FOR UPDATE`: si dos traspasos llegan a la vez, el segundo espera a que
    # termine el primero y lee el estado que dejó. `populate_existing` para
    # que esa lectura venga de la base y no de lo que la sesión ya tenía.
    pieza = db.get(Pieza, pieza_id, with_for_update=True, populate_existing=True)
    if pieza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # L4: el otro la movió antes, o la pantalla de quien pide era vieja.
    if pieza.estado != pedido.desde:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "La pieza cambió de estado mientras la mirabas. "
                "Recarga para ver dónde está."
            ),
        )

    # L5: el estado y su fila de historia van en la misma transacción.
    pieza.estado = hacia
    traspaso = Traspaso(
        pieza_id=pieza.id,
        transicion=pedido.transicion,
        desde=pedido.desde,
        hacia=hacia,
        creado_por=usuario.usuario,
        nota=pedido.nota,
    )
    db.add(traspaso)
    db.commit()
    db.refresh(traspaso)

    return traspaso
