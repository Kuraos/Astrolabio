"""Modelo de datos.

Los nombres del dominio van en español (CLAUDE.md §4): `usuario`, `rol` son
las palabras que usan las dos personas y las mismas del vault.

Los estados del flujo salen de `docs/estados-del-flujo.md`, que recoge con sus
palabras la conversación con el editor que pide el §2.8. Ninguno entra aquí sin
pasar antes por ese documento.
"""

from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Único: sin esto, sembrar dos veces crea un segundo «johan» y el login
    # elige uno de los dos según el humor del planificador de consultas.
    usuario: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hash_password: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sesiones: Mapped[list["Sesion"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class Sesion(Base):
    """Sesión con estado (ADR 0006).

    El `id` **es** la credencial: el valor opaco que viaja en la cookie. Por
    eso no es autoincremental ni un UUID, sino aleatoriedad criptográfica —
    un identificador adivinable sería una cuenta regalada.
    """

    __tablename__ = "sesion"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        # La cascada evita sesiones huérfanas: sin ella, una cookie apuntando
        # a un usuario borrado sería un 500 en vez de un 401.
        ForeignKey("usuario.id", ondelete="CASCADE"),
        index=True,
    )
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    usuario: Mapped[Usuario] = relationship(back_populates="sesiones")


# Los de `docs/estados-del-flujo.md` §2, en el orden del flujo, con el
# identificador que guardan la base y el vault (ADR 0009): minúscula, sin
# tildes y con guion bajo. En pantalla se leen las palabras del documento.
ESTADOS = (
    "investigacion",
    "solicitud_entregada",
    "material_aprobado",
    "finalizada",
    "diseno_aprobado",
    "publicada",
)

# De quién es la pieza en cada estado (§2 del documento). `publicada` no es de
# nadie: Johan la publica desde `diseno_aprobado`, y después el flujo terminó.
DE_QUIEN_ES = {
    "investigacion": "investigador",
    "solicitud_entregada": "investigador",
    "material_aprobado": "editor",
    "finalizada": "investigador",
    "diseno_aprobado": "investigador",
    "publicada": None,
}


class Pieza(Base):
    """La pieza de contenido: nació en C1, creció en H1 y ganó estado en K1.

    El estado llegó cuando la conversación con el editor que pide el §2.8 ya
    estaba escrita, y no antes. Solo lo mueve un traspaso (K3).
    """

    __tablename__ = "pieza"
    # K2 en la base y no solo en el código: un estado fuera de la lista no entra
    # ni por SQL directo. Añadir uno pide migración, que es cuando la guía de la
    # conversación dice que se añade: «cuando el hábito exista, con su propia
    # migración».
    __table_args__ = (
        CheckConstraint(
            "estado IN ({})".format(", ".join(f"'{e}'" for e in ESTADOS)),
            name="ck_pieza_estado",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Quién la creó sale de la sesión, nunca del cuerpo de la petición: si lo
    # mandara el cliente, cualquiera podría atribuirle una pieza al otro.
    creada_por: Mapped[str] = mapped_column(String(50))

    # `Text` y no `String(n)`: un guion no tiene longitud máxima razonable, y
    # un límite inventado se descubre truncando el trabajo de alguien.
    # Cadena vacía en vez de nulo — una pieza sin guion todavía no es un caso
    # especial, es una pieza recién creada.
    guion: Mapped[str] = mapped_column(Text, server_default="", default="")

    # El cuadro de materiales del editor (Fase 8, AN1–AN4): «tipo de pieza»
    # es `formato`, y «destino», `plataforma`. En pantalla, sus palabras; aquí
    # y en el vault, los identificadores (ADR 0015). Las listas cerradas las
    # impone la API, como el tema. Nulos mientras no se decidan: al crear una
    # pieza rara vez se sabe ya para qué es o a qué nivel va.
    formato: Mapped[str | None] = mapped_column(String(20), default=None)
    tema: Mapped[str | None] = mapped_column(String(100), default=None)
    proposito: Mapped[str | None] = mapped_column(String(20), default=None)
    nivel: Mapped[str | None] = mapped_column(String(20), default=None)
    # Una lista y no un valor: lo que va a TikTok se publica tal cual en
    # Instagram (fase 8, §8.1). Sin destino todavía, la lista vacía.
    plataforma: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)), server_default="{}", default=list
    )

    # AN5: los textos del cuadro, aparte del guion. El copy gráfico, uno por
    # lámina —el largo se cuenta por lámina, que es donde el editor lo sufre
    # (§8.2)—, y el caption de la publicación. `Text`, como el guion.
    copy_grafico: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default="{}", default=list
    )
    caption: Mapped[str] = mapped_column(Text, server_default="", default="")

    # Nombres de notas `literature` del vault, que alimentan `investigacion:`
    # y `## Respaldo científico` al exportar (ADR 0001).
    #
    # Una lista y no una tabla con clave foránea: esas notas viven en el vault
    # y Astrolabio no las posee, así que no hay integridad referencial que
    # imponer. Fingirla con una tabla propia sería mentir sobre quién manda.
    respaldo: Mapped[list[str]] = mapped_column(
        ARRAY(String(200)), server_default="{}", default=list
    )

    # Y2: etiquetas libres, para saber de qué se ha hablado. Llegan
    # normalizadas por la API (ADR 0011), así que aquí solo se guardan.
    # `Text` como el guion: un tope inventado se descubriría con un 500.
    etiquetas: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default="{}", default=list
    )

    # AC1: la entrega del diseño —la «fecha de entrega» del editor— y la
    # publicación prevista. Días del calendario, sin hora ni zona: un `date`
    # no se corre de día al pasar de UTC a Bogotá, como sí `creada_en`.
    # Nulas mientras no se decidan.
    fecha_entrega: Mapped[date | None] = mapped_column(Date, default=None)
    fecha_publicacion_prevista: Mapped[date | None] = mapped_column(Date, default=None)

    # Toda pieza nace en la etapa de Johan, con el nombre que le puso él (K1).
    estado: Mapped[str] = mapped_column(
        String(30), server_default="investigacion", default="investigacion"
    )

    # AF1: el exportador busca aquí el día en que se publicó. Solo lectura: la
    # historia se escribe en `traspasos.py`, y `viewonly` impide que la pieza
    # la toque, ni siquiera anulando su clave al borrarse, que sería un
    # `UPDATE` que el trigger rechaza (ADR 0008).
    traspasos: Mapped[list["Traspaso"]] = relationship(
        order_by="Traspaso.id", viewonly=True
    )

    @property
    def de_quien_es(self) -> str | None:
        """El rol al que le toca, o nadie si ya se publicó (K4)."""
        return DE_QUIEN_ES[self.estado]


class Traspaso(Base):
    """Una fila cada vez que una pieza cambia de estado (M1).

    Es el historial de quién cambió qué, «la mitad del valor del producto»
    (§2.3), y de él sale la métrica del §2.6: cuánto tarda una pieza en cada
    etapa. Por eso es append-only, y no por disciplina: un trigger de Postgres
    rechaza `UPDATE`, `DELETE` y `TRUNCATE` (ADR 0008).
    """

    __tablename__ = "traspaso"

    id: Mapped[int] = mapped_column(primary_key=True)
    pieza_id: Mapped[int] = mapped_column(ForeignKey("pieza.id"), index=True)
    transicion: Mapped[str] = mapped_column(String(30))
    desde: Mapped[str] = mapped_column(String(30))
    hacia: Mapped[str] = mapped_column(String(30))
    # Como `creada_por` en la pieza: sale de la sesión, nunca del cuerpo de la
    # petición, o cualquiera podría atribuirle un traspaso al otro.
    creado_por: Mapped[str] = mapped_column(String(50))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Opcional. Existe por `devolver`: sin decir qué ajustar, cada devolución
    # termina en un mensaje de «¿qué ajusto?», que es lo que el §1 quiere
    # eliminar.
    nota: Mapped[str | None] = mapped_column(Text, default=None)


class Tarea(Base):
    """Una tarea (AD1): de la checklist de una pieza, o suelta si no tiene.

    No es historia, a diferencia de `traspaso`: se marca, se desmarca y se
    borra, como el material, y por eso no está en el §2.6.
    """

    __tablename__ = "tarea"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Opcional: sin pieza, la tarea es suelta (decisión 1 de la Fase 6).
    pieza_id: Mapped[int | None] = mapped_column(
        ForeignKey("pieza.id"), index=True, default=None
    )
    texto: Mapped[str] = mapped_column(Text)
    # Nulos mientras está pendiente: estar hecha es tenerlos, y no una columna
    # aparte que pudiera contradecirlos.
    marcada_por: Mapped[str | None] = mapped_column(String(50), default=None)
    marcada_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    # Como `creada_por` en la pieza: sale de la sesión, nunca del cuerpo.
    creada_por: Mapped[str] = mapped_column(String(50))
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    @property
    def hecha(self) -> bool:
        return self.marcada_en is not None


class Enlace(Base):
    """Un enlace de referencia de la pieza: un pin, un vídeo, un artículo (P1).

    Es material que se comparte, no historia: se añade y se quita, a diferencia
    de `traspaso`. Las imágenes no van aquí; viven en la carpeta de la pieza en
    Syncthing (ADR 0010).
    """

    __tablename__ = "enlace"

    id: Mapped[int] = mapped_column(primary_key=True)
    pieza_id: Mapped[int] = mapped_column(ForeignKey("pieza.id"), index=True)
    # `Text`, como el guion: un límite inventado se descubre cortando la URL de
    # alguien. Que sea `http` o `https` lo valida la API (P3).
    url: Mapped[str] = mapped_column(Text)
    nota: Mapped[str | None] = mapped_column(Text, default=None)
    # Como `creada_por` en la pieza: sale de la sesión, nunca del cuerpo.
    creado_por: Mapped[str] = mapped_column(String(50))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Boceto(Base):
    """Un boceto de la pieza, pedido a Claude (Fase 9, ADR 0016).

    Cada intento que llegó a tener respuesta, también el que falló: los dos
    cuestan, y el gasto que se ve tiene que ser el real (AU1). Uno válido
    guarda sus láminas; uno fallido, por qué falló. Nunca los dos, ni ninguno.
    No es historia del §2.6, pero tampoco se edita: se pide otro.
    """

    __tablename__ = "boceto"
    __table_args__ = (
        CheckConstraint(
            "(laminas IS NULL) <> (error IS NULL)", name="ck_boceto_laminas_o_error"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pieza_id: Mapped[int] = mapped_column(ForeignKey("pieza.id"), index=True)
    # Como `creada_por` en la pieza: sale de la sesión, nunca del cuerpo.
    creado_por: Mapped[str] = mapped_column(String(50))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # El que respondió, que con el respaldo ante una negativa puede no ser el
    # que se pidió.
    modelo: Mapped[str] = mapped_column(String(100))
    # La rejilla con que se pidió: el boceto se dibuja con ella aunque la
    # pieza cambie de tipo después.
    columnas: Mapped[int] = mapped_column(Integer)
    filas: Mapped[int] = mapped_column(Integer)
    # El copy con que se hizo, para decir si el de la pieza cambió después.
    copy_grafico: Mapped[list[str]] = mapped_column(ARRAY(Text))
    # `none_as_null`: sin él, un `None` se guarda como el JSON `null`, que para
    # Postgres no es nulo, y la restricción de arriba lo rechazaría.
    laminas: Mapped[list | None] = mapped_column(JSONB(none_as_null=True), default=None)
    # AT5: las cifras del boceto que no están en el guion ni en el copy.
    avisos: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default="{}", default=list
    )
    error: Mapped[str | None] = mapped_column(Text, default=None)
    tokens_entrada: Mapped[int] = mapped_column(Integer)
    tokens_salida: Mapped[int] = mapped_column(Integer)
