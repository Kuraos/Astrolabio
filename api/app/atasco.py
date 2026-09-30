"""Dónde se atasca cada pieza (Fase 10, AX1–AX5; PRD §8.2).

Es la métrica del §2.6: cuánto tarda cada etapa. Sale entera de `traspaso`,
que es de solo inserción justo para esto (ADR 0008), y de `creada_en`.

Sin agregados: con pocas piezas publicadas, una mediana por etapa mide el azar,
como el ranking de temas del ADR 0004 (decisión 4 de la fase). Cada pieza va
con sus tiempos, y quien mira compara.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from .auth import usuario_actual
from .db import get_db
from .models import ESTADOS, Pieza, Traspaso, Usuario

router = APIRouter(prefix="/api/atasco", tags=["atasco"])


@dataclass
class Tiempos:
    # Segundos en cada estado por el que pasó, en el orden del flujo y sin
    # `publicada`: ahí ya no se espera a nadie.
    etapas: dict[str, float]
    # Los de la estancia de ahora, o `None` si ya se publicó.
    en_estado: float | None
    # De la primera entrega a la publicación, o hasta ahora si sigue en curso;
    # `None` si nunca se entregó (AX5).
    ciclo: float | None
    devoluciones: int
    reformulaciones: int


def tiempos(creada_en: datetime, historia: Sequence[Traspaso], ahora: datetime) -> Tiempos:
    """AX2–AX5, sobre la historia de una pieza en orden de `id`.

    `creado_en` es la hora en que empezó cada transacción, así que un traspaso
    puede llevar una marca anterior al que lo precede (M3). Contar desde la
    marca más alta vista hasta ese momento, y no desde la del traspaso
    anterior, deja cada tramo en cero o más (AX4) sin inventar tiempo: la suma
    de las etapas sigue siendo la vida de la pieza (AX3).
    """
    acumulado: dict[str, timedelta] = {}
    estado = "investigacion"  # toda pieza nace ahí (K1)
    desde = creada_en
    primera_entrega: datetime | None = None
    fin: datetime | None = None
    vueltas = {"devolver": 0, "reformular": 0}

    for paso in historia:
        cuando = max(desde, paso.creado_en)
        acumulado[estado] = acumulado.get(estado, timedelta()) + (cuando - desde)
        estado, desde = paso.hacia, cuando
        if paso.transicion == "entregar" and primera_entrega is None:
            primera_entrega = cuando
        if paso.transicion in vueltas:
            vueltas[paso.transicion] += 1
        if estado == "publicada":
            fin = cuando

    en_estado = None
    if fin is None:
        ahora = max(desde, ahora)
        acumulado[estado] = acumulado.get(estado, timedelta()) + (ahora - desde)
        en_estado = (ahora - desde).total_seconds()

    return Tiempos(
        etapas={e: acumulado[e].total_seconds() for e in ESTADOS if e in acumulado},
        en_estado=en_estado,
        ciclo=(
            None
            if primera_entrega is None
            else ((fin or ahora) - primera_entrega).total_seconds()
        ),
        devoluciones=vueltas["devolver"],
        reformulaciones=vueltas["reformular"],
    )


class Etapa(BaseModel):
    estado: str
    segundos: float


class AtascoDePieza(BaseModel):
    """Solo los tiempos: el título, el estado, el turno y las etiquetas ya los
    trae `GET /api/piezas`, y el cliente las junta por `pieza_id`.
    """

    pieza_id: int
    etapas: list[Etapa]
    en_estado: float | None
    ciclo: float | None
    devoluciones: int
    reformulaciones: int


@router.get("", response_model=list[AtascoDePieza])
def atasco(
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> list[AtascoDePieza]:
    """AX1: los dos roles lo ven entero, como el tablero.

    Dos consultas —las piezas y todas sus historias— y no una por pieza.
    """
    ahora = datetime.now(timezone.utc)
    piezas = db.query(Pieza).options(selectinload(Pieza.traspasos)).order_by(Pieza.id).all()

    filas = []
    for pieza in piezas:
        t = tiempos(pieza.creada_en, pieza.traspasos, ahora)
        filas.append(
            AtascoDePieza(
                pieza_id=pieza.id,
                etapas=[Etapa(estado=e, segundos=s) for e, s in t.etapas.items()],
                en_estado=t.en_estado,
                ciclo=t.ciclo,
                devoluciones=t.devoluciones,
                reformulaciones=t.reformulaciones,
            )
        )
    return filas
