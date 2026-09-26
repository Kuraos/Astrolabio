"""Bocetos con Claude (criterios AS–AU de la Fase 9, ADR 0016).

El primer servicio externo de Astrolabio. La API le pide a Claude el boceto
de cada lámina con una salida estructurada, lo valida y lo guarda; el cliente
lo dibuja desde los datos. Sin clave, la app es la de siempre y el panel lo
dice.

La llamada al SDK vive sola en `pedir_a_claude`, y el resto recibe una
`Respuesta` sin nada del SDK: así las pruebas simulan a Claude sin red y sin
gastar.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from itertools import combinations
from typing import Literal

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from .auth import usuario_actual
from .config import settings
from .db import get_db
from .models import Boceto, Pieza, Usuario

router = APIRouter(prefix="/api/piezas", tags=["bocetos"])

# §7.1 de la fase: (columnas, filas), de celdas cuadradas. Un tipo que no está
# aquí no tiene boceto todavía.
REJILLAS: dict[str, tuple[int, int]] = {
    # 4:5, 1080 × 1350 px: celdas de 90 px.
    "carrusel": (12, 15),
    "post_individual": (12, 15),
    # Proporción A, 1:√2: 12 × 16,97.
    "poster": (12, 17),
}
_DE_UNA_LAMINA = {"post_individual": "Un post individual", "poster": "Un póster"}

# Lo que admite Instagram en un carrusel (fase 9, §8.11).
MAX_LAMINAS = 20


class Zona(BaseModel):
    """Un rectángulo de celdas: su esquina de arriba a la izquierda, contada
    desde 1, y su alto y su ancho en celdas."""

    fila: int = Field(ge=1)
    col: int = Field(ge=1)
    filas: int = Field(ge=1)
    cols: int = Field(ge=1)


class Elemento(BaseModel):
    tipo: Literal["titulo", "dato", "texto", "formula", "figura", "grafica", "nota"]
    peso: Literal[1, 2, 3, 4]
    contenido: str
    zona: Zona


class Lamina(BaseModel):
    numero: int
    idea: str
    elementos: list[Elemento]
    nota_para_la_edicion: str


class BocetoDeClaude(BaseModel):
    laminas: list[Lamina]


# AS3: el esquema que se envía sale del mismo modelo con que se valida. Lo que
# la API no admite —los mínimos de la zona— el SDK lo deja como pista en la
# descripción, y lo comprueba Pydantic al validar.
ESQUEMA = anthropic.transform_schema(BocetoDeClaude)

SISTEMA = """\
Haces bocetos de piezas gráficas de Voz del Cosmos, un proyecto de divulgación \
astronómica en español. Un boceto no es el diseño: dice qué elementos lleva cada \
lámina, cuál pesa más y dónde va cada uno, para que el editor, que hace el \
diseño, empiece con la composición resuelta.

Cada lámina se compone sobre una rejilla de celdas cuadradas; la pieza dice \
cuántas columnas y filas tiene. Una zona es un rectángulo de celdas: `fila` y \
`col` son su esquina de arriba a la izquierda, contadas desde 1, y `filas` y \
`cols`, su alto y su ancho. Las zonas de una lámina no se solapan ni se salen de \
la rejilla. No hace falta llenarla: el aire también compone.

Los elementos son de siete tipos: titulo; dato, una cifra o un hecho que se \
destaca; texto; formula; figura, una imagen; grafica, un gráfico de datos; y \
nota, un crédito, una fuente o una aclaración pequeña.

El peso ordena la jerarquía: 1 es lo primero que se ve y 4, lo último. Cada \
lámina tiene exactamente un elemento de peso 1.

El contenido sale del copy gráfico de esa lámina y del guion. No inventes \
cifras, datos ni afirmaciones: una cifra que no está en el copy ni en el guion \
no va. Las fórmulas van en LaTeX, sin los signos $. En una figura o una \
gráfica, el contenido describe qué imagen o qué datos lleva, según el guion.

Haz una lámina por cada lámina del copy, en su orden, numeradas desde 1. La \
idea resume en una frase qué comunica la lámina, y la nota para la edición es \
un consejo breve y concreto para el editor sobre ella.
"""


@dataclass
class Respuesta:
    """Lo que interesa de la respuesta de Claude, sin tipos del SDK."""

    texto: str
    modelo: str
    tokens_entrada: int
    tokens_salida: int
    # El `stop_reason`: `end_turn` si terminó; `max_tokens` o `refusal`, si no.
    fin: str | None


Dibujante = Callable[[str], Respuesta]


@lru_cache
def _cliente(clave: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=clave)


def pedir_a_claude(cliente: anthropic.Anthropic, modelo: str, mensaje: str) -> Respuesta:
    """AS3 y AS4: una petición, con la salida estructurada del esquema.

    En streaming, porque un carrusel largo, con razonamiento, no cabe en los
    16.000 tokens de una petición sin él (fase 9, §8.11). Y con el respaldo
    ante una negativa (§8.12): si el modelo declina, la API reintenta con otro
    dentro de la misma petición, y `modelo` dice cuál respondió.
    """
    with cliente.beta.messages.stream(
        model=modelo,
        max_tokens=64000,
        system=SISTEMA,
        messages=[{"role": "user", "content": mensaje}],
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        final = stream.get_final_message()

    return Respuesta(
        texto=next((bloque.text for bloque in final.content if bloque.type == "text"), ""),
        modelo=final.model,
        tokens_entrada=final.usage.input_tokens,
        tokens_salida=final.usage.output_tokens,
        fin=final.stop_reason,
    )


def dibujante() -> Dibujante | None:
    """AS5: sin clave no hay quien dibuje, y la app sigue igual."""
    if not settings.anthropic_api_key:
        return None
    cliente = _cliente(settings.anthropic_api_key)
    return lambda mensaje: pedir_a_claude(cliente, settings.bocetos_modelo, mensaje)


def mensaje_para_claude(pieza: Pieza, columnas: int, filas: int) -> str:
    """AS2: lo que sale hacia Claude, y nada más: el título, el cuadro, el
    tema, el copy gráfico y el guion (fase 9, §7.3). Ni el respaldo, que es
    del vault, ni las notas del traspaso, ni quién la hizo.
    """
    cuadro = "\n".join(
        [
            f"Título: {pieza.titulo}",
            f"Tipo de pieza: {pieza.formato}",
            f"Destinos: {', '.join(pieza.plataforma) or 'sin decidir'}",
            f"Propósito: {pieza.proposito or 'sin decidir'}",
            f"Nivel: {pieza.nivel or 'sin decidir'}",
            f"Tema: {pieza.tema or 'sin decidir'}",
            f"Rejilla: {columnas} columnas × {filas} filas",
            f"Láminas: {len(pieza.copy_grafico)}",
        ]
    )
    laminas = "\n\n".join(
        f"### Lámina {numero}\n\n{texto.strip() or '(sin texto)'}"
        for numero, texto in enumerate(pieza.copy_grafico, 1)
    )
    guion = pieza.guion.strip() or "(sin guion)"
    return f"{cuadro}\n\n## Copy gráfico\n\n{laminas}\n\n## Guion\n\n{guion}\n"


def por_que_no(pieza: Pieza, dibujar: Dibujante | None) -> str | None:
    """AS5 y AS6: por qué no se puede pedir un boceto ahora, o `None` si sí.
    Lo primero, el despliegue; después, la pieza.
    """
    if dibujar is None:
        return (
            "Los bocetos no están configurados en este despliegue: falta "
            "ANTHROPIC_API_KEY en el .env."
        )
    if not pieza.formato:
        return "Elige el tipo de pieza en el cuadro de materiales: el boceto se hace en su rejilla."
    if pieza.formato not in REJILLAS:
        return (
            "Los bocetos son para carruseles, posts individuales y pósteres. "
            "El short y el video largo, más adelante."
        )
    if not any(lamina.strip() for lamina in pieza.copy_grafico):
        return "Escribe y guarda el copy gráfico: el boceto se hace lámina por lámina."
    if pieza.formato in _DE_UNA_LAMINA and len(pieza.copy_grafico) > 1:
        return (
            f"{_DE_UNA_LAMINA[pieza.formato]} es una lámina, y el copy gráfico "
            f"tiene {len(pieza.copy_grafico)}: déjalo en una."
        )
    if len(pieza.copy_grafico) > MAX_LAMINAS:
        return (
            f"El boceto se pide para {MAX_LAMINAS} láminas como mucho, y el copy "
            f"gráfico tiene {len(pieza.copy_grafico)}."
        )
    return None


def _se_solapan(a: Zona, b: Zona) -> bool:
    """Dos rectángulos de celdas comparten al menos una."""
    return (
        a.col < b.col + b.cols
        and b.col < a.col + a.cols
        and a.fila < b.fila + b.filas
        and b.fila < a.fila + a.filas
    )


def validar(boceto: BocetoDeClaude, columnas: int, filas: int, laminas: int) -> list[str]:
    """AT1–AT4: lo que el esquema no puede exigir. Devuelve lo que falla, en
    minúscula para ir a media frase, o nada si el boceto vale.
    """
    fallos = []
    if len(boceto.laminas) != laminas:
        fallos.append(f"trae {len(boceto.laminas)} láminas y el copy tiene {laminas}")

    for indice, lamina in enumerate(boceto.laminas, 1):
        if lamina.numero != indice:
            fallos.append(f"la lámina {indice} viene numerada {lamina.numero}")
        if not lamina.elementos:
            fallos.append(f"la lámina {indice} no tiene elementos")
            continue

        principales = sum(1 for elemento in lamina.elementos if elemento.peso == 1)
        if principales != 1:
            fallos.append(
                f"la lámina {indice} tiene {principales} elementos de peso 1, y debe tener uno"
            )

        for elemento in lamina.elementos:
            zona = elemento.zona
            if zona.col + zona.cols - 1 > columnas or zona.fila + zona.filas - 1 > filas:
                fallos.append(f"en la lámina {indice}, {elemento.tipo} se sale de la rejilla")

        for a, b in combinations(lamina.elementos, 2):
            if _se_solapan(a.zona, b.zona):
                fallos.append(f"en la lámina {indice}, {a.tipo} y {b.tipo} se solapan")

    return fallos


_CIFRA = re.compile(r"\d+")


def cifras_sin_fuente(boceto: BocetoDeClaude, fuente: str) -> list[str]:
    """AT5: las cifras del boceto que no están en el guion ni en el copy.

    Se comparan las rachas de dígitos, así que la misma cifra escrita de otra
    forma no avisa: «1{,}496» en el LaTeX del copy y «1,496» en el boceto dan
    las mismas, «1» y «496». Avisa y no rechaza (fase 9, §8.10).
    """
    conocidas = set(_CIFRA.findall(fuente))
    avisos = []
    for lamina in boceto.laminas:
        nuevas = {
            cifra
            for elemento in lamina.elementos
            for cifra in _CIFRA.findall(elemento.contenido)
        } - conocidas
        if nuevas:
            verbo = "está" if len(nuevas) == 1 else "están"
            lista = ", ".join(sorted(nuevas, key=int))
            avisos.append(f"Lámina {lamina.numero}: {lista} no {verbo} en el guion ni en el copy.")
    return avisos


def _leer(respuesta: Respuesta, columnas: int, filas: int, laminas: int) -> BocetoDeClaude | str:
    """El boceto de la respuesta, o por qué no vale (AT6)."""
    if respuesta.fin == "refusal":
        return "Claude declinó hacer este boceto."
    if respuesta.fin == "max_tokens":
        return "El boceto se cortó antes de terminar: el copy es demasiado largo para una sola petición."
    try:
        boceto = BocetoDeClaude.model_validate_json(respuesta.texto)
    except ValidationError:
        return "La respuesta de Claude no tiene la forma de un boceto. Pídelo otra vez."
    fallos = validar(boceto, columnas, filas, laminas)
    if fallos:
        return f"El boceto de Claude no vale: {'; '.join(fallos)}. Pídelo otra vez."
    return boceto


class BocetoPublico(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    creado_por: str
    creado_en: datetime
    modelo: str
    columnas: int
    filas: int
    copy_grafico: list[str]
    laminas: list[Lamina]
    avisos: list[str]
    tokens_entrada: int
    tokens_salida: int


class EstadoDeLosBocetos(BaseModel):
    """AU2: si se puede pedir uno y por qué no, como el respaldo (G4), y los
    válidos, del más nuevo al más viejo."""

    disponible: bool
    motivo: str | None = None
    bocetos: list[BocetoPublico] = []


def _buscar(db: Session, pieza_id: int) -> Pieza:
    pieza = db.get(Pieza, pieza_id)
    if pieza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return pieza


@router.get("/{pieza_id}/bocetos", response_model=EstadoDeLosBocetos)
def ver_bocetos(
    pieza_id: int,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
    dibujar: Dibujante | None = Depends(dibujante),
) -> EstadoDeLosBocetos:
    """Los dos roles los ven."""
    pieza = _buscar(db, pieza_id)
    validos = (
        db.query(Boceto)
        .filter(Boceto.pieza_id == pieza.id, Boceto.laminas.is_not(None))
        .order_by(Boceto.id.desc())
        .all()
    )
    motivo = por_que_no(pieza, dibujar)
    return EstadoDeLosBocetos(
        disponible=motivo is None,
        motivo=motivo,
        bocetos=[BocetoPublico.model_validate(boceto) for boceto in validos],
    )


# AS7: lo que responde Anthropic, dicho para quien lo lee en la pieza.
_FALLOS_DE_ANTHROPIC: list[tuple[type[Exception], str]] = [
    (anthropic.AuthenticationError, "Anthropic no acepta la clave: revisa ANTHROPIC_API_KEY en el .env."),
    (anthropic.RateLimitError, "Anthropic pide esperar: van demasiadas peticiones seguidas. Prueba en un minuto."),
    (anthropic.APIStatusError, "La API de Anthropic falló. Prueba otra vez en un rato."),
    (
        anthropic.APIConnectionError,
        "No se pudo hablar con Anthropic: revisa la conexión a internet del PC donde corre Astrolabio.",
    ),
]


@router.post(
    "/{pieza_id}/bocetos",
    response_model=BocetoPublico,
    status_code=status.HTTP_201_CREATED,
)
def pedir_boceto(
    pieza_id: int,
    usuario: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
    dibujar: Dibujante | None = Depends(dibujante),
) -> BocetoPublico:
    """AS1: los dos roles (fase 9, §7.2). Nunca solo: siempre a petición.

    Se hace con lo que está guardado de la pieza, no con lo que alguien tenga
    a medio escribir. Un intento con respuesta se guarda aunque falle, porque
    costó (AU1); uno que no llegó a Anthropic, no.
    """
    pieza = _buscar(db, pieza_id)
    motivo = por_que_no(pieza, dibujar)
    if motivo is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=motivo)

    columnas, filas = REJILLAS[pieza.formato]
    try:
        respuesta = dibujar(mensaje_para_claude(pieza, columnas, filas))
    except anthropic.APIError as exc:
        # La primera clase que coincide: de la más concreta a la más general.
        detalle = next(
            (texto for clase, texto in _FALLOS_DE_ANTHROPIC if isinstance(exc, clase)),
            "La API de Anthropic falló. Prueba otra vez en un rato.",
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detalle) from exc

    boceto = Boceto(
        pieza_id=pieza.id,
        creado_por=usuario.usuario,
        modelo=respuesta.modelo,
        columnas=columnas,
        filas=filas,
        copy_grafico=list(pieza.copy_grafico),
        tokens_entrada=respuesta.tokens_entrada,
        tokens_salida=respuesta.tokens_salida,
    )
    leido = _leer(respuesta, columnas, filas, len(pieza.copy_grafico))

    if isinstance(leido, str):
        boceto.error = leido
        db.add(boceto)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=leido)

    boceto.laminas = [lamina.model_dump() for lamina in leido.laminas]
    boceto.avisos = cifras_sin_fuente(leido, "\n".join([pieza.guion, *pieza.copy_grafico]))
    db.add(boceto)
    db.commit()
    db.refresh(boceto)
    return BocetoPublico.model_validate(boceto)
