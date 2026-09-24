"""El material de la pieza (criterios P, Q y R de la Fase 3).

Lo que Johan le pasa al editor para hacer la pieza, y que hoy va por chat. Los
enlaces viven en la base. Las imágenes, en la carpeta de la pieza en Syncthing
y en su calidad original (ADR 0010): el editor las necesita en sus programas
de diseño, y los binarios no entran a la aplicación (§2.2).

Los dos roles añaden y quitan material: es justo lo que se comparte. Sin
sesión, 401, como todo lo demás (C5).

En la carpeta compartida, este módulo escribe una sola cosa: el `mkdir` de la
carpeta de cada pieza (Q5). No crea, mueve, renombra ni borra archivos, y una
prueba recorre su árbol sintáctico para que siga así.
"""

import io
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Response, status
from PIL import Image, ImageOps
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .config import settings
from .db import get_db
from .models import Enlace, Pieza, Usuario
from .respaldo import dentro_de

router = APIRouter(prefix="/api/piezas", tags=["material"])

# Syncthing la pone en la raíz de cada carpeta que comparte. Si falta, la ruta
# configurada no es la compartida —una errata en el `.env`, que Docker
# convierte en una carpeta vacía— y lo que la app creara ahí no le llegaría a
# nadie.
MARCA_DE_SYNCTHING = ".stfolder"

# Lo que Windows no admite en un nombre (ADR 0010), más los caracteres de
# control. La carpeta se crea en la máquina de Johan y se abre en la del editor.
_PROHIBIDOS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

# R1: tienen miniatura estas extensiones y ninguna más (R4).
IMAGENES = {".jpg", ".jpeg", ".png", ".webp"}

# Los decodificadores que Pillow puede probar. Un archivo que se llama `.png`
# y no lo es no llega a los formatos raros, que son los menos revisados.
_FORMATOS = ("JPEG", "PNG", "WEBP")

# 400 px de lado alcanzan para una rejilla de miniaturas en una pantalla de
# doble densidad. El tope es la excepción del §2.2: menos de 200 kB.
LADO_DE_MINIATURA = 400
TOPE_DE_MINIATURA = 200_000


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


# --- Q: la carpeta de la pieza en Syncthing ---


class Archivo(BaseModel):
    nombre: str
    tamano: int
    modificado: datetime
    # R2: la URL lleva la fecha de modificación, así que cambia cuando cambia
    # el archivo, y mientras tanto el navegador la guarda. `None` si el
    # archivo no es una imagen (R4).
    miniatura: str | None = None


class EstadoDeLaCarpeta(BaseModel):
    """Como el respaldo (G4): que no haya carpeta no es un error, y el panel
    dice por qué. Sin `motivo` y sin `carpeta`, la pieza aún no tiene la suya
    y el panel ofrece crearla (Q3).
    """

    motivo: str | None = None
    carpeta: str | None = None
    archivos: list[Archivo] = []


def carpeta_compartida() -> Path | None:
    """La ruta del entorno, o `None` si no se configuró (Q1)."""
    ruta = settings.material_path
    return Path(ruta) if ruta else None


def nombre_de_carpeta(pieza: Pieza) -> str:
    """`<id> - <título>`, sin lo que Windows no admite (ADR 0010).

    Windows tampoco admite un nombre que acabe en punto o en espacio. Y si del
    título no queda nada, el nombre sigue empezando por `<id> - `, que es por
    donde la app lo encuentra.
    """
    titulo = _PROHIBIDOS.sub("", pieza.titulo).strip(". ")
    return f"{pieza.id} - {titulo or 'sin título'}"


def _carpetas_de_la_pieza(base: Path, pieza_id: int) -> list[Path]:
    """Por el número y no por el nombre: el título cambia, la carpeta no (Q2).

    El separador va en el prefijo para que la pieza 1 no se quede con la
    carpeta de la 12.
    """
    prefijo = f"{pieza_id} - "
    return sorted(
        c
        for c in base.iterdir()
        if c.name.startswith(prefijo) and c.is_dir() and dentro_de(base, c)
    )


def _archivos(carpeta: Path, pieza_id: int) -> list[Archivo]:
    """Q3, en el orden del explorador. Q4: un enlace simbólico que se salga
    de la carpeta de la pieza no se lee, ni siquiera su tamaño.
    """
    archivos = []
    for archivo in sorted(carpeta.iterdir(), key=lambda a: a.name.casefold()):
        if not archivo.is_file() or not dentro_de(carpeta, archivo):
            continue
        datos = archivo.stat()
        miniatura = None
        if archivo.suffix.lower() in IMAGENES:
            consulta = urlencode({"nombre": archivo.name, "v": datos.st_mtime_ns})
            miniatura = f"/api/piezas/{pieza_id}/carpeta/miniatura?{consulta}"
        archivos.append(
            Archivo(
                nombre=archivo.name,
                tamano=datos.st_size,
                modificado=datetime.fromtimestamp(datos.st_mtime, UTC),
                miniatura=miniatura,
            )
        )
    return archivos


def estado_de_la_carpeta(base: Path | None, pieza_id: int) -> EstadoDeLaCarpeta:
    if base is None:
        return EstadoDeLaCarpeta(
            motivo="Syncthing no está configurado en este despliegue."
        )

    if not (base / MARCA_DE_SYNCTHING).exists():
        return EstadoDeLaCarpeta(
            motivo="La ruta configurada no es la carpeta de Syncthing: le falta "
            f"«{MARCA_DE_SYNCTHING}». Revisa SYNCTHING_HOST_PATH en el .env."
        )

    carpetas = _carpetas_de_la_pieza(base, pieza_id)

    if len(carpetas) > 1:
        # ADR 0010: la app no adivina cuál es la buena.
        nombres = ", ".join(f"«{c.name}»" for c in carpetas)
        return EstadoDeLaCarpeta(
            motivo=f"Hay {len(carpetas)} carpetas con el número {pieza_id}: "
            f"{nombres}. Deja una y la app la encuentra."
        )

    if not carpetas:
        return EstadoDeLaCarpeta()

    return EstadoDeLaCarpeta(
        carpeta=carpetas[0].name, archivos=_archivos(carpetas[0], pieza_id)
    )


@router.get("/{pieza_id}/carpeta", response_model=EstadoDeLaCarpeta)
def ver_carpeta(
    pieza_id: int,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> EstadoDeLaCarpeta:
    _pieza(db, pieza_id)
    return estado_de_la_carpeta(carpeta_compartida(), pieza_id)


@router.post("/{pieza_id}/carpeta", response_model=EstadoDeLaCarpeta)
def crear_carpeta(
    pieza_id: int,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> EstadoDeLaCarpeta:
    """Q5: lo único que la app escribe en la carpeta compartida. La crea
    cualquiera de los dos (decisión 5).

    Solo si la pieza no tiene ya la suya, aunque lleve un título viejo: dos
    carpetas para una pieza es justo lo que el ADR 0010 no sabe resolver.
    """
    pieza = _pieza(db, pieza_id)
    base = carpeta_compartida()
    estado = estado_de_la_carpeta(base, pieza_id)
    if base is None or estado.motivo or estado.carpeta:
        return estado

    (base / nombre_de_carpeta(pieza)).mkdir(exist_ok=True)
    return estado_de_la_carpeta(base, pieza_id)


# --- R: miniaturas ---


def miniatura(archivo: Path) -> bytes:
    """R1 y R2: un WebP de 400 px como mucho, hecho al vuelo y sin guardarlo.

    WebP y no JPEG, para no perder la transparencia de un logo. La calidad
    solo baja si hace falta para caber en el tope. Medido con ruido puro, lo
    que peor se comprime: a calidad 80 y con transparencia pesa 245 kB, a 60
    ya cabe (168 kB) y a 0 se queda en 45 kB. Una foto real cabe a la primera.
    """
    with Image.open(archivo, formats=_FORMATOS) as imagen:
        # Primero reducir: un JPEG se decodifica ya a escala, sin cargarlo
        # entero en memoria.
        imagen.thumbnail((LADO_DE_MINIATURA, LADO_DE_MINIATURA))
        # El móvil guarda la foto de lado y apunta en el EXIF cómo girarla.
        imagen = ImageOps.exif_transpose(imagen)

        if imagen.mode.startswith("I"):
            # Un PNG de 16 bits, como los de un procesado astronómico. Pillow
            # los recorta a 255 al pasarlos a 8 bits y la miniatura sale
            # blanca: se reescala entre el mínimo y el máximo.
            imagen = imagen.convert("I")
            bajo, alto = imagen.getextrema()
            escala = 255 / max(alto - bajo, 1)
            imagen = imagen.point(lambda v: (v - bajo) * escala).convert("L")

        if imagen.mode not in ("RGB", "RGBA"):
            imagen = imagen.convert("RGBA" if imagen.has_transparency_data else "RGB")

        for calidad in (80, 60, 40, 20, 0):
            salida = io.BytesIO()
            imagen.save(salida, "WEBP", quality=calidad, alpha_quality=calidad)
            if salida.tell() < TOPE_DE_MINIATURA:
                return salida.getvalue()

    raise RuntimeError("La miniatura no cabe en el tope del §2.2")


@router.get("/{pieza_id}/carpeta/miniatura")
def ver_miniatura(
    pieza_id: int,
    nombre: str,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> Response:
    """La miniatura de una imagen de la carpeta de la pieza.

    `nombre` es un nombre de archivo, no una ruta: con un `../` o un enlace
    simbólico que se salga de la carpeta de la pieza, 404 (Q4). La `v` de la
    URL no se lee; está para que la URL cambie cuando cambia el archivo (R2).
    """
    _pieza(db, pieza_id)
    base = carpeta_compartida()
    estado = estado_de_la_carpeta(base, pieza_id)
    if base is None or estado.carpeta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    carpeta = base / estado.carpeta
    archivo = carpeta / nombre
    if (
        Path(nombre).name != nombre
        or archivo.suffix.lower() not in IMAGENES
        or not archivo.is_file()
        or not dentro_de(carpeta, archivo)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        datos = miniatura(archivo)
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        # Un archivo a medio llegar, o que no es la imagen que dice ser.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se pudo leer la imagen.",
        ) from exc

    # `private`: la miniatura pide sesión y no la guarda nadie más que el
    # navegador de quien la pidió. Con la fecha en la URL, puede ser eterna.
    return Response(
        content=datos,
        media_type="image/webp",
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )
