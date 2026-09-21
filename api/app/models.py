"""Modelo de datos.

Los nombres del dominio van en español (CLAUDE.md §4): `usuario`, `rol` son
las palabras que usan las dos personas y las mismas del vault.

Los estados del flujo salen de `docs/estados-del-flujo.md`, que recoge con sus
palabras la conversación con el editor que pide el §2.8. Ninguno entra aquí sin
pasar antes por ese documento.
"""

from datetime import datetime

from sqlalchemy import ARRAY, CheckConstraint, DateTime, ForeignKey, String, Text, func
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

    # Toda pieza nace en la etapa de Johan, con el nombre que le puso él (K1).
    estado: Mapped[str] = mapped_column(
        String(30), server_default="investigacion", default="investigacion"
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
