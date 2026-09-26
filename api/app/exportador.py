"""Exportador al vault (criterios I1–I5, O1, AA1 y AF1, ADR 0001, 0007, 0009, 0011
y 0012).

La mitad «Astrolabio → vault». Una sola dirección: el vault recibe una copia
marcada como generada que nunca se edita a mano.

Escribe en exactamente dos sitios: la carpeta `Contenido/` y el archivo
`MOC-VozDelCosmos.md`. `Investigacion/` está montada en solo lectura, así que
ahí no puede escribir aunque el código se equivoque (ADR 0007).
"""

from datetime import date, datetime
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
from .material import nombre_sin_prohibidos
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


def _dia_local(momento: datetime) -> date:
    """La fecha del vault es la del calendario de Johan, no la de UTC.

    Devuelve un `date` y no una cadena: `yaml.safe_dump` escribe las cadenas
    entrecomilladas, y la plantilla del vault usa fechas sin comillas. Una
    nota generada debe ser indistinguible de una escrita a mano (ADR 0001).
    """
    return momento.astimezone(ZoneInfo(settings.vault_zona_horaria)).date()


def _fecha_publicacion(pieza: Pieza) -> date | None:
    """AF1 (ADR 0012): la prevista mientras no se publica; publicada, la real,
    que es el día del traspaso «Publicar» en la zona del vault.

    Una pieza publicada sin ese traspaso solo sale de tocar la base a mano;
    ahí se queda la prevista, en vez de reventar la exportación.
    """
    if pieza.estado == "publicada":
        publicar = next((t for t in pieza.traspasos if t.transicion == "publicar"), None)
        if publicar is not None:
            return _dia_local(publicar.creado_en)
    return pieza.fecha_publicacion_prevista


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
        # El estado al exportar, con el mismo identificador de la base y sin
        # traducirlo (ADR 0009). Es una copia: envejece hasta la exportación
        # siguiente, igual que el guion.
        "status": pieza.estado,
        "fecha": _dia_local(pieza.creada_en),
        "fecha_publicacion": _fecha_publicacion(pieza),
        "plataforma": pieza.plataforma,
        "investigacion": list(pieza.respaldo),
        "metricas": {"vistas": None, "alcance": None},
        # Cada etiqueta, anidada bajo el tag de siempre, que se queda: el panel
        # de tags de Obsidian las agrupa ahí (ADR 0011).
        "tags": ["voz-del-cosmos", *(f"voz-del-cosmos/{e}" for e in pieza.etiquetas)],
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


def _enlazar_en_moc(base: Path, nombre: str, anterior: str | None = None) -> None:
    """Añade el enlace en la sección propia, sin tocar las escritas a mano.

    Al nombre del archivo, no al título: es lo que Obsidian resuelve. Si la
    nota se renombró, el enlace a su nombre `anterior` sale de la sección.
    """
    moc = base / MOC
    if not moc.is_file():
        return

    texto = moc.read_text(encoding="utf-8")
    enlace = f"- [[{nombre}]]"

    if SECCION_MOC not in texto:
        if enlace not in texto:
            texto = f"{texto.rstrip()}\n\n{SECCION_MOC}\n\n{enlace}\n"
            moc.write_text(texto, encoding="utf-8")
        return

    cabeza, resto = texto.split(SECCION_MOC, 1)
    # La sección acaba en el encabezado siguiente: lo que venga después es de Johan.
    seccion, corte, cola = resto.partition("\n#")
    if anterior is not None:
        seccion = seccion.replace(f"\n- [[{anterior}]]", "")
    if enlace not in texto:
        # El nuevo, primero, y cada enlace en su línea.
        seccion = f"\n\n{enlace}\n" + seccion.lstrip("\n")

    nuevo = f"{cabeza}{SECCION_MOC}{seccion}{corte}{cola}"
    if nuevo != texto:
        moc.write_text(nuevo, encoding="utf-8")


def exportar(pieza: Pieza, base: Path) -> Path:
    carpeta = base / CARPETA
    carpeta.mkdir(parents=True, exist_ok=True)

    # El vault vive en Windows, y un `/` sacaría la nota de `Contenido/` (ADR 0007).
    nombre = nombre_sin_prohibidos(pieza.titulo)
    destino = carpeta / f"{nombre}.md"
    previa = _nota_previa(carpeta, pieza.id)

    # El título cambió: se mueve la nota anterior en vez de dejar dos.
    anterior = None
    if previa is not None and previa != destino:
        previa.rename(destino)
        anterior = previa.stem

    if destino.is_file() and MARCA not in destino.read_text(encoding="utf-8"):
        raise NotaAjena(
            f"«{destino.name}» existe y no lleva la marca de generada: "
            "lo escribió una persona y Astrolabio no lo sobrescribe."
        )

    destino.write_text(_nota(pieza), encoding="utf-8")
    _enlazar_en_moc(base, nombre, anterior)

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
