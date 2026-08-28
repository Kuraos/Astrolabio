"""Piezas y su autorización (criterios C1–C5, H1–H3).

El §2.3 no admite matices: cada endpoint comprueba el rol **en el servidor**.
Que la aplicación viva en una red privada no cambia nada — los dos roles del
§1 necesitan identidad para funcionar, y el historial de quién hizo qué es la
mitad del valor del producto.
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .db import get_db
from .models import Pieza, Usuario

router = APIRouter(prefix="/api/piezas", tags=["piezas"])

# Los cuatro que pregunta la plantilla del vault. Aceptar cualquier cadena
# dejaría que un dedazo llegara al frontmatter de una nota generada.
Formato = Literal["reel", "carrusel", "video", "post"]


class PiezaNueva(BaseModel):
    titulo: str
    formato: Formato | None = None
    tema: str | None = None
    plataforma: str | None = None


class PiezaEditada(BaseModel):
    """Todo opcional: es un `PATCH`, y lo que no venga se queda como está.

    Distinguir «no lo mandaron» de «lo mandaron vacío» importa aquí: borrar un
    guion por omitirlo del cuerpo sería una forma muy cara de aprender la
    diferencia.
    """

    titulo: str | None = None
    guion: str | None = None
    formato: Formato | None = None
    tema: str | None = None
    plataforma: str | None = None
    respaldo: list[str] | None = None


class PiezaPublica(BaseModel):
    """Sin campo `estado`, como el modelo: §2.8 sigue vigente."""

    model_config = {"from_attributes": True}

    id: int
    titulo: str
    creada_en: datetime
    creada_por: str
    guion: str
    formato: str | None
    tema: str | None
    plataforma: str | None
    respaldo: list[str]


def _solo_investigador(usuario: Usuario) -> None:
    """403 y no otra cosa: significa «sé quién eres y no puedes».

    Un 401 diría que no se sabe quién es, y un 404 escondería que la ruta
    existe.
    """
    if usuario.rol != "investigador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


def _buscar(db: Session, pieza_id: int) -> Pieza:
    pieza = db.get(Pieza, pieza_id)
    if pieza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return pieza


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


@router.get("/{pieza_id}", response_model=PiezaPublica)
def ver_pieza(
    pieza_id: int,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Pieza:
    """Los dos roles leen el guion. El editor necesita saber de qué va la
    pieza para poder editarla en vídeo; lo que no hace es escribirlo.
    """
    return _buscar(db, pieza_id)


@router.post("", response_model=PiezaPublica, status_code=status.HTTP_201_CREATED)
def crear_pieza(
    nueva: PiezaNueva,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Pieza:
    """C2: solo `investigador`."""
    _solo_investigador(usuario)

    pieza = Pieza(
        titulo=nueva.titulo,
        formato=nueva.formato,
        tema=nueva.tema,
        plataforma=nueva.plataforma,
        creada_por=usuario.usuario,
    )
    db.add(pieza)
    db.commit()
    db.refresh(pieza)

    return pieza


@router.patch("/{pieza_id}", response_model=PiezaPublica)
def editar_pieza(
    pieza_id: int,
    cambios: PiezaEditada,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Pieza:
    """Los dos roles editan la pieza. El respaldo científico, solo Johan.

    El guion lo escriben ambos: es una decisión del dueño del producto, no
    una deducción a partir del §1 — deducirla fue inventarme el dominio, que
    es lo que el §2.8 prohíbe.

    `respaldo` es la excepción, y no por jerarquía: el ADR 0001 le da
    `literature` solo a Johan y H4 ya le devuelve 403 al editor en
    `/api/respaldo`. Dejarle escribir ese campo sería permitirle enlazar
    notas de una lista que no puede ver.
    """
    pieza = _buscar(db, pieza_id)

    cambios_pedidos = cambios.model_dump(exclude_unset=True)

    if "respaldo" in cambios_pedidos:
        _solo_investigador(usuario)

    # Solo lo que vino en el cuerpo: el guion no se borra por no mencionarlo.
    for campo, valor in cambios_pedidos.items():
        setattr(pieza, campo, valor)

    db.commit()
    db.refresh(pieza)

    return pieza
