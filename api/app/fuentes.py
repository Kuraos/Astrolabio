"""Una fuente nueva, creada desde Astrolabio (criterios BB de la Fase 12).

La única excepción al «el vault manda, Astrolabio lee» del ADR 0001, y por eso
vive aparte de `respaldo.py`, que sigue sin poder escribir (ADR 0019). Aquí se
**crea** una nota `literature` en `Investigacion/Recursos/`, y nada más: no se
edita, no se renombra y no se borra. Desde que nace, la nota es del vault.

Que no pise nada lo impone el sistema de archivos: se abre en modo `x`, que
falla si el archivo ya existe.
"""

from datetime import datetime, timezone
from typing import Literal

import yaml
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from . import respaldo
from .auth import usuario_actual
from .db import get_db
from .exportador import _ROMPEN_ENLACES, _dia_local
from .material import nombre_sin_prohibidos
from .models import Pieza, Usuario

router = APIRouter(prefix="/api/fuentes", tags=["fuentes"])

# Las tres palabras del `CLAUDE.md` de la carpeta del vault, como quedan
# escritas en `## Nivel de confianza científica`.
CONFIANZA = {
    "consenso": "Consenso establecido.",
    "hipotesis": "Hipótesis activa.",
    "preliminar": "Resultado preliminar.",
}


class FuenteNueva(BaseModel):
    fuente_titulo: str = Field(min_length=1, max_length=300)
    # El nombre de la nota en el vault. Vacío, el título de la fuente.
    nombre: str = Field(default="", max_length=200)
    fuente_tipo: Literal["paper", "articulo"]
    autor: str = Field(default="", max_length=300)
    # Un enlace o un DOI. Sin él la nota no dice de dónde sale, y el vault
    # pide citar la fuente por URL.
    url: str = Field(min_length=1, max_length=2000)
    resumen: str = ""
    confianza: Literal["consenso", "hipotesis", "preliminar"]
    # La pieza desde la que se crea, para dejarla enlazada de una vez.
    pieza_id: int | None = None

    @field_validator("fuente_titulo", "nombre", "autor", "url")
    @classmethod
    def _una_linea(cls, texto: str) -> str:
        texto = texto.strip()
        if "\n" in texto or "\r" in texto:
            raise ValueError("va en una sola línea")
        return texto

    @field_validator("fuente_titulo")
    @classmethod
    def _con_titulo(cls, titulo: str) -> str:
        if not titulo:
            raise ValueError("falta el título de la fuente")
        return titulo

    @field_validator("url")
    @classmethod
    def _enlace(cls, url: str) -> str:
        # Un DOI suelto, `10.xxxx/…`, se guarda como su enlace.
        if url.startswith("10."):
            url = f"https://doi.org/{url}"
        if not url.startswith(("http://", "https://")) or any(c.isspace() for c in url):
            raise ValueError("pega un enlace http(s) o un DOI")
        return url


def _nota(fuente: FuenteNueva) -> str:
    """La nota como la pide el `CLAUDE.md` de la carpeta: el frontmatter de
    `literature` y sus tres secciones.
    """
    resumen = fuente.resumen.strip()
    frontmatter = {
        "type": "literature",
        "cssclasses": ["vh-literature"],
        "fuente_titulo": fuente.fuente_titulo,
        "fuente_tipo": fuente.fuente_tipo,
        **({"autor": fuente.autor} if fuente.autor else {}),
        # Sin resumen, nadie la ha procesado todavía.
        "status": "leido" if resumen else "por-leer",
        "fecha": _dia_local(datetime.now(timezone.utc)),
        "tags": ["voz-del-cosmos"],
    }
    cabecera = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=None,
        width=10_000,
    )
    return (
        f"---\n{cabecera}---\n\n"
        f"## Resumen\n\n{resumen + chr(10) + chr(10) if resumen else ''}"
        f"Fuente: {fuente.url}\n\n"
        f"## Nivel de confianza científica\n\n{CONFIANZA[fuente.confianza]}\n\n"
        "## Relacionado\n\n- [[MOC-VozDelCosmos]]\n"
    )


@router.post("", response_model=respaldo.Respaldo, status_code=status.HTTP_201_CREATED)
def crear_fuente(
    fuente: FuenteNueva,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> respaldo.Respaldo:
    """BB1: solo el `investigador`, como todo el respaldo (H4)."""
    if usuario.rol != "investigador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    pieza = None
    if fuente.pieza_id is not None:
        pieza = db.get(Pieza, fuente.pieza_id)
        if pieza is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    base = respaldo.carpeta_configurada()
    estado = respaldo.estado_del_respaldo(base)
    if base is None or not estado.disponible:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=estado.motivo)

    # La misma limpieza que la nota exportada (ADR 0007): sin lo que Windows no
    # admite ni lo que rompe un `[[enlace]]`.
    nombre = nombre_sin_prohibidos(_ROMPEN_ENLACES.sub("", fuente.nombre or fuente.fuente_titulo))
    destino = base / respaldo.SUBCARPETA / f"{nombre}.md"
    if not respaldo.dentro_de(base, destino):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    try:
        # `x`: crear o fallar. Nunca se pisa una nota del vault (ADR 0019).
        with destino.open("x", encoding="utf-8", newline="\n") as archivo:
            archivo.write(_nota(fuente))
    except FileExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya hay una nota llamada «{nombre}» en el vault: ponle otro nombre.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se pudo escribir en el vault: {type(exc).__name__}",
        ) from exc

    if pieza is not None and nombre not in pieza.respaldo:
        pieza.respaldo = [*pieza.respaldo, nombre]
        db.commit()

    return next(n for n in respaldo.listar_respaldo(base) if n.archivo == nombre)
