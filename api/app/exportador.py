"""Exportador al vault (criterios I1–I5, ADR 0001 y ADR 0007).

La mitad «Astrolabio → vault». Una sola dirección: el vault recibe una copia
marcada como generada que nunca se edita a mano.

Escribe en exactamente dos sitios: la carpeta `Contenido/` y el archivo
`MOC-VozDelCosmos.md`. `Investigacion/` está montada en solo lectura, así que
ahí no puede escribir aunque el código se equivoque (ADR 0007).
"""

from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import respaldo
from .auth import usuario_actual
from .config import settings
from .db import get_db
from .models import Pieza, Usuario

router = APIRouter(prefix="/api/piezas", tags=["piezas"])

CARPETA = "Contenido"
MOC = "MOC-VozDelCosmos.md"
MARCA = "<!-- generado por Astrolabio — no editar -->"
SECCION_MOC = "## Piezas (generado por Astrolabio)"


class NotaAjena(Exception):
    """El archivo existe y no lo escribió Astrolabio."""


class Exportacion(BaseModel):
    archivo: str


def _frontmatter(texto: str) -> dict:
    try:
        return yaml.safe_load(texto.split("---", 2)[1]) or {}
    except (IndexError, yaml.YAMLError):
        return {}


CHECKLIST = """\
- [ ] Cada afirmación del guion tiene una nota de respaldo enlazada arriba
- [ ] El nivel de confianza (consenso establecido / hipótesis activa / resultado preliminar) se refleja en el lenguaje del guion, no solo en la nota fuente
- [ ] Cifras, unidades y órdenes de magnitud coinciden con la fuente
- [ ] Créditos de imagen y video resueltos
"""


def _fecha_local(pieza: Pieza) -> date:
    """La fecha del vault es la del calendario de Johan, no la de UTC.

    Devuelve un `date` y no una cadena: `yaml.safe_dump` escribe las cadenas
    entrecomilladas, y la plantilla del vault usa fechas sin comillas. Una
    nota generada debe ser indistinguible de una escrita a mano (ADR 0001).
    """
    return pieza.creada_en.astimezone(ZoneInfo(settings.vault_zona_horaria)).date()


def _cuerpo_del_guion(guion: str) -> str:
    """El encabezado lo pone el exportador, no el texto.

    Si el guion ya trae `## Guion` —porque se escribió copiando la plantilla—
    se le quita, para que la nota no acabe con la sección duplicada.
    """
    texto = guion.strip()
    if texto.startswith("## Guion"):
        texto = texto[len("## Guion") :].lstrip()
    return texto


def _nota(pieza: Pieza) -> str:
    """La nota completa, con el frontmatter que pide la plantilla del vault."""
    cabecera = {
        "type": "contenido",
        "cssclasses": ["vh-contenido"],
        "formato": pieza.formato,
        "tema": pieza.tema,
        # `idea` mientras no exista la máquina de estados: la pieza no tiene
        # `estado` (§2.8) y este campo hay que escribirlo con algo. Cuando los
        # estados existan, saldrán de aquí.
        "status": "idea",
        "fecha": _fecha_local(pieza),
        "fecha_publicacion": None,
        "plataforma": pieza.plataforma,
        "investigacion": list(pieza.respaldo),
        "metricas": {"vistas": None, "alcance": None},
        "tags": ["voz-del-cosmos"],
        # Lo que permite reencontrar la nota si cambia el título (ADR 0007).
        "fuente": "astrolabio",
        "astrolabio_id": pieza.id,
    }

    enlaces = "\n".join(f"- [[{a}]]" for a in pieza.respaldo) or "- "

    return (
        "---\n"
        + yaml.safe_dump(cabecera, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + f"{MARCA}\n\n"
        + f"# {pieza.titulo}\n\n"
        + f"## Respaldo científico\n\n{enlaces}\n\n"
        + f"## Guion\n\n{_cuerpo_del_guion(pieza.guion)}\n\n"
        # La checklist es parte del flujo descrito en el `CLAUDE.md` de la
        # carpeta; perderla al exportar la borraría del proceso.
        + f"## Verificación antes de publicar\n\n{CHECKLIST}\n"
        + "## Notas de producción\n\n"
        + "## Relacionado\n\n- [[MOC-VozDelCosmos]]\n"
    )


def _nota_previa(carpeta: Path, pieza_id: int) -> Path | None:
    """Busca una nota generada para esta pieza, aunque el título haya cambiado."""
    for archivo in carpeta.glob("*.md"):
        if _frontmatter(archivo.read_text(encoding="utf-8")).get("astrolabio_id") == pieza_id:
            return archivo
    return None


def _enlazar_en_moc(base: Path, titulo: str) -> None:
    """Añade el enlace en la sección propia, sin tocar las escritas a mano."""
    moc = base / MOC
    if not moc.is_file():
        return

    texto = moc.read_text(encoding="utf-8")
    enlace = f"- [[{titulo}]]"

    if enlace in texto:
        return

    if SECCION_MOC in texto:
        cabeza, resto = texto.split(SECCION_MOC, 1)
        texto = f"{cabeza}{SECCION_MOC}\n{enlace}{resto[len(chr(10)):] if resto.startswith(chr(10)) else resto}"
    else:
        texto = f"{texto.rstrip()}\n\n{SECCION_MOC}\n\n{enlace}\n"

    moc.write_text(texto, encoding="utf-8")


def exportar(pieza: Pieza, base: Path) -> Path:
    carpeta = base / CARPETA
    carpeta.mkdir(parents=True, exist_ok=True)

    destino = carpeta / f"{pieza.titulo}.md"
    previa = _nota_previa(carpeta, pieza.id)

    # El título cambió: se mueve la nota anterior en vez de dejar dos.
    if previa is not None and previa != destino:
        previa.rename(destino)

    if destino.is_file() and MARCA not in destino.read_text(encoding="utf-8"):
        raise NotaAjena(
            f"«{destino.name}» existe y no lleva la marca de generada: "
            "lo escribió una persona y Astrolabio no lo sobrescribe."
        )

    destino.write_text(_nota(pieza), encoding="utf-8")
    _enlazar_en_moc(base, pieza.titulo)

    return destino


@router.post("/{pieza_id}/exportar", response_model=Exportacion)
def exportar_pieza(
    pieza_id: int,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Exportacion:
    """El destino es el vault personal de Johan, así que solo él exporta."""
    if usuario.rol != "investigador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    pieza = db.get(Pieza, pieza_id)
    if pieza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # A través del módulo y no con la función importada: `from x import f`
    # congela la referencia en el momento del import, y entonces sustituirla
    # en `respaldo` no afecta aquí — una diferencia invisible hasta que muerde.
    base = respaldo.carpeta_configurada()
    if base is None or not base.is_dir():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El vault no está montado en este despliegue.",
        )

    try:
        destino = exportar(pieza, base)
    except NotaAjena as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se pudo escribir en el vault: {type(exc).__name__}",
        ) from exc

    return Exportacion(archivo=str(destino))
