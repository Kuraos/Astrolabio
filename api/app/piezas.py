"""Piezas y su autorización (criterios C1–C5, H1–H3, K4, Y1–Y4 y AC1–AC2).

El §2.3 no admite matices: cada endpoint comprueba el rol **en el servidor**.
Que la aplicación viva en una red privada no cambia nada — los dos roles del
§1 necesitan identidad para funcionar, y el historial de quién hizo qué es la
mitad del valor del producto.
"""

import re
import unicodedata
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .db import get_db
from .models import Pieza, Usuario
from .traspasos import transiciones_posibles

router = APIRouter(prefix="/api/piezas", tags=["piezas"])

# Los cuatro que pregunta la plantilla del vault. Aceptar cualquier cadena
# dejaría que un dedazo llegara al frontmatter de una nota generada.
Formato = Literal["reel", "carrusel", "video", "post"]

# Y1: los cuatro temas de la Fase 5 (§7.1). El ADR 0004 pide pocos y fijos
# para que las celdas tema × formato × plataforma junten `n`: un tema nuevo
# por un dedazo partiría las métricas.
Tema = Literal["Sistema Solar", "Estrellas", "Galaxias y cosmología", "Exploración espacial"]

_TILDES = str.maketrans("áéíóúü", "aeiouu")
_SEPARADORES = re.compile(r"[\s/]+")
_NO_ADMITIDO = re.compile(r"[^\w-]")
_GUIONES = re.compile(r"-{2,}")


def normalizar_etiqueta(texto: str) -> str:
    """Y3: una etiqueta que Obsidian reconozca como tag (ADR 0011).

    Primero se compone (NFC): hay teclados que escriben la ñ como una n más una
    tilde combinante, y sin componerla la tilde se perdería con el resto de lo
    que no es letra. Después, minúsculas; espacios y `/` a guiones, porque la
    jerarquía la pone el exportador; sin tildes pero con ñ, para que
    «cosmología» y «cosmologia» sean la misma; y fuera lo que no sea letra,
    número, `_` o `-`.

    `ValueError` si queda vacía o es solo números: Obsidian no la reconocería.
    """
    etiqueta = unicodedata.normalize("NFC", texto).strip().lower().translate(_TILDES)
    etiqueta = _SEPARADORES.sub("-", etiqueta)
    etiqueta = _NO_ADMITIDO.sub("", etiqueta)
    etiqueta = _GUIONES.sub("-", etiqueta).strip("-")
    if not etiqueta or etiqueta.isdigit():
        raise ValueError("una etiqueta necesita al menos una letra")
    return etiqueta


class PiezaNueva(BaseModel):
    titulo: str
    formato: Formato | None = None
    tema: Tema | None = None
    plataforma: str | None = None


class PiezaEditada(BaseModel):
    """Todo opcional: es un `PATCH`, y lo que no venga se queda como está.

    Distinguir «no lo mandaron» de «lo mandaron vacío» importa aquí: borrar un
    guion por omitirlo del cuerpo sería una forma muy cara de aprender la
    diferencia.

    Opcional no es anulable: solo `formato`, `tema`, `plataforma` y las dos
    fechas admiten `null`, porque una pieza puede no tenerlos todavía, y `null`
    es cómo se borran (AC2). En el resto la columna no admite nulos, y un
    `null` explícito sería un 500 de la base en vez de un 422. Sus valores por
    defecto no se escriben nunca —`exclude_unset` deja fuera lo que no vino—:
    solo permiten omitirlos.
    """

    titulo: str = ""
    guion: str = ""
    formato: Formato | None = None
    tema: Tema | None = None
    plataforma: str | None = None
    respaldo: list[str] = []
    etiquetas: list[str] = []
    # AC2: los dos roles, y `null` la borra. Pydantic rechaza con 422 lo que no
    # sea un día: otro formato, un día que no existe o una hora.
    fecha_entrega: date | None = None
    fecha_publicacion_prevista: date | None = None

    @field_validator("etiquetas")
    @classmethod
    def _normalizar(cls, etiquetas: list[str]) -> list[str]:
        """Y3: en el servidor, no en el formulario. Sin repetidas, en el orden
        en que llegaron.
        """
        return list(dict.fromkeys(normalizar_etiqueta(e) for e in etiquetas))


class PiezaPublica(BaseModel):
    """La pieza como la ve quien pregunta (K4).

    `estado` y `de_quien_es` son de la pieza; `transiciones`, de la pieza y de
    quien pregunta. Las tres salen del servidor para que el cliente no deduzca
    nada: la tabla de transiciones vive en un solo sitio.
    """

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
    etiquetas: list[str]
    fecha_entrega: date | None
    fecha_publicacion_prevista: date | None
    estado: str
    de_quien_es: str | None
    # La rellena `_publica`: depende de quién pregunta, y la pieza no lo sabe.
    transiciones: list[str] = []


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


def _publica(pieza: Pieza, usuario: Usuario) -> PiezaPublica:
    publica = PiezaPublica.model_validate(pieza)
    publica.transiciones = transiciones_posibles(pieza.estado, usuario.rol)
    return publica


@router.get("", response_model=list[PiezaPublica])
def listar_piezas(
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> list[PiezaPublica]:
    """C3: los dos roles ven la misma lista. Solo cambian las `transiciones`,
    que dependen de quién pregunta (K4).
    """
    piezas = db.query(Pieza).order_by(Pieza.creada_en.desc()).all()
    return [_publica(pieza, usuario) for pieza in piezas]


@router.get("/{pieza_id}", response_model=PiezaPublica)
def ver_pieza(
    pieza_id: int,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> PiezaPublica:
    """Los dos roles leen el guion. El editor necesita saber de qué va la
    pieza para poder editarla en vídeo; lo que no hace es escribirlo.
    """
    return _publica(_buscar(db, pieza_id), usuario)


@router.post("", response_model=PiezaPublica, status_code=status.HTTP_201_CREATED)
def crear_pieza(
    nueva: PiezaNueva,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> PiezaPublica:
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

    return _publica(pieza, usuario)


@router.patch("/{pieza_id}", response_model=PiezaPublica)
def editar_pieza(
    pieza_id: int,
    cambios: PiezaEditada,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> PiezaPublica:
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

    return _publica(pieza, usuario)
