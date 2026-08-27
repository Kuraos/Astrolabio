"""Respaldo científico: el vault manda, Astrolabio lee (criterios G1–G4, H4).

La mitad «vault → Astrolabio» del [ADR 0001]. Aquí **no se escribe nada**, y
esa restricción está sostenida por tres cosas distintas, a propósito:

1. El montaje del contenedor es de solo lectura (`:ro` en `compose.yaml`), así
   que el sistema operativo lo impide aunque el código se equivoque.
2. Una prueba recorre el árbol sintáctico de este módulo y falla si aparece
   una llamada de escritura.
3. El exportador de la Fase I vivirá en **otro módulo** y con su propia
   carpeta, para que la separación siga siendo visible en el código.

La primera es la que de verdad protege; las otras dos existen para que romper
la regla requiera hacerlo a propósito.
"""

from datetime import date
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .auth import usuario_actual
from .config import settings
from .models import Usuario

router = APIRouter(prefix="/api/respaldo", tags=["respaldo"])

# La estructura la fija el `CLAUDE.md` de la carpeta del vault, no nosotros.
SUBCARPETA = Path("Investigacion") / "Recursos"

_SEPARADOR = "---"


class Respaldo(BaseModel):
    """Índice de una nota, no su contenido.

    Traerse el texto completo de cada nota sería mover el vault a la API por
    si acaso. Cuando haga falta leer una, se leerá esa.
    """

    archivo: str
    fuente_titulo: str
    fuente_tipo: str | None = None
    autor: str | None = None
    fecha: date | None = None


class EstadoDelRespaldo(BaseModel):
    """G4: el vault puede no estar, y eso no es un error.

    Vive en la máquina de Johan y es su carpeta personal. El taller tiene que
    funcionar igual sin él —el editor entra y trabaja— y decir por qué no hay
    respaldo en vez de fallar.
    """

    disponible: bool
    motivo: str | None = None
    notas: list[Respaldo] = []


def carpeta_configurada() -> Path | None:
    """La ruta del entorno, o `None` si no se configuró."""
    ruta = settings.vault_voz_del_cosmos_path
    return Path(ruta) if ruta else None


def dentro_de(base: Path, candidato: Path) -> bool:
    """¿`candidato` queda bajo `base` una vez resueltos los enlaces?

    Se resuelve antes de comparar porque el ataque real no es un `../` en una
    petición: es un enlace simbólico dentro de la carpeta. `resolve()` lo
    sigue sin avisar, y al otro lado está el resto del vault personal de
    Johan — el diario incluido (§2.5).
    """
    try:
        return candidato.resolve().is_relative_to(base.resolve())
    except (OSError, ValueError):
        return False


def _frontmatter(texto: str) -> dict | None:
    """Extrae el bloque YAML inicial.

    Con un parser de YAML y no partiendo por el primer `:`. Los títulos reales
    del vault llevan dos puntos dentro de las comillas —
    `"GWTC-5.0: Updated LIGO–Virgo–KAGRA Catalog…"`— y el troceo a mano los
    corta por la mitad sin que nadie se entere.
    """
    if not texto.startswith(_SEPARADOR):
        return None

    partes = texto.split(_SEPARADOR, 2)
    if len(partes) < 3:
        return None

    try:
        datos = yaml.safe_load(partes[1])
    except yaml.YAMLError:
        # Una nota con el frontmatter roto se ignora; no tumba el listado.
        return None

    return datos if isinstance(datos, dict) else None


def listar_respaldo(base: Path) -> list[Respaldo]:
    """Las notas `literature` de la carpeta, ordenadas por fecha descendente."""
    carpeta = base / SUBCARPETA
    if not carpeta.is_dir():
        return []

    notas: list[Respaldo] = []

    for archivo in sorted(carpeta.glob("*.md")):
        if not dentro_de(base, archivo):
            continue

        datos = _frontmatter(archivo.read_text(encoding="utf-8"))

        # Solo `literature`: es lo único sobre lo que el ADR 0001 le da
        # autoridad al vault. Una `contenido` aquí sería la copia generada por
        # Astrolabio leyéndose a sí misma.
        if not datos or datos.get("type") != "literature":
            continue

        titulo = datos.get("fuente_titulo")
        if not titulo:
            # `fuente_titulo` es obligatorio para `literature` según las reglas
            # de la carpeta; sin él la nota ya sale marcada en su auditoría.
            continue

        notas.append(
            Respaldo(
                archivo=archivo.stem,
                fuente_titulo=str(titulo),
                fuente_tipo=datos.get("fuente_tipo"),
                autor=datos.get("autor"),
                fecha=datos.get("fecha"),
            )
        )

    return sorted(notas, key=lambda n: (n.fecha is None, n.fecha), reverse=True)


def estado_del_respaldo(base: Path | None) -> EstadoDelRespaldo:
    if base is None:
        return EstadoDelRespaldo(
            disponible=False,
            motivo="El vault no está configurado en este despliegue.",
        )

    if not (base / SUBCARPETA).is_dir():
        return EstadoDelRespaldo(
            disponible=False,
            motivo=f"No encuentro «{SUBCARPETA.as_posix()}» en la ruta configurada.",
        )

    return EstadoDelRespaldo(disponible=True, notas=listar_respaldo(base))


@router.get("", response_model=EstadoDelRespaldo)
def ver_respaldo(usuario: Usuario = Depends(usuario_actual)) -> EstadoDelRespaldo:
    """H4: solo el `investigador`.

    El ADR 0001 le asigna `literature` a Johan y solo a Johan, porque son
    notas de su vault personal. El editor recibe 403 — no un panel escondido,
    que según §2.3 es decoración y no autorización.
    """
    if usuario.rol != "investigador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return estado_del_respaldo(carpeta_configurada())
