"""Modelo de datos.

Los nombres del dominio van en español (CLAUDE.md §4): `usuario`, `rol` son
las palabras que usan las dos personas y las mismas del vault.

Aquí **no** hay estados de flujo, y no es un olvido: §2.8 dice que la máquina
de estados sale de una conversación con el editor, usando sus palabras, y esa
conversación todavía no ha ocurrido.
"""

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text, func
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


class Pieza(Base):
    """Entidad mínima del criterio C1.

    **Sin campo `estado`, y es deliberado.** El §2.8 dice que los estados del
    flujo salen de una conversación con el editor, usando sus palabras para su
    propio trabajo. Esa conversación no ha ocurrido, así que modelarlos ahora
    sería inventarlos — y es la parte divertida, que por eso es la que se hace
    demasiado pronto.
    """

    __tablename__ = "pieza"

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

    # Los tres salen de la plantilla del vault, no de nuestra imaginación.
    # Nulos mientras no se decidan: al crear una pieza rara vez se sabe ya en
    # qué plataforma acaba.
    formato: Mapped[str | None] = mapped_column(String(20), default=None)
    tema: Mapped[str | None] = mapped_column(String(100), default=None)
    plataforma: Mapped[str | None] = mapped_column(String(50), default=None)

    # Nombres de notas `literature` del vault, que alimentan `investigacion:`
    # y `## Respaldo científico` al exportar (ADR 0001).
    #
    # Una lista y no una tabla con clave foránea: esas notas viven en el vault
    # y Astrolabio no las posee, así que no hay integridad referencial que
    # imponer. Fingirla con una tabla propia sería mentir sobre quién manda.
    respaldo: Mapped[list[str]] = mapped_column(
        ARRAY(String(200)), server_default="{}", default=list
    )
