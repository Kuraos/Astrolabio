"""la pieza gana el cuadro de materiales

Criterios AN1–AN5 de `docs/fase-8-cuadro-de-materiales.md`: lo que pide el
cuadro de materiales del editor. En pantalla se leen sus palabras; en la base
y en el vault, estos identificadores (ADR 0015).

Dos columnas cambian y cuatro llegan:

- `formato` cambia de valores: `reel` pasa a `short`, `video` a
  `video_largo` y `post` a `post_individual`. `carrusel` se queda, y
  `poster` es nuevo.
- `plataforma` pasa de texto a lista, porque lo que va a TikTok se publica
  tal cual en Instagram (§8.1). Un valor que reconoce, sin distinguir
  mayúsculas ni espacios alrededor, pasa a ser una lista de uno; vacío o
  nulo, la lista vacía.
- `proposito` y `nivel`, nulos mientras no se decidan, como el tema.
- `copy_grafico`, un texto por lámina, y `caption`. Vacíos por defecto,
  como el guion.

Un valor que no sabe convertir **detiene la migración** y lo nombra, en los
dos sentidos: perderlo en silencio sería peor que no migrar. Al deshacerla,
lo que la versión anterior no sabe guardar —un póster, o más de un
destino— también la detiene. Todo corre en una transacción, así que una
parada no deja nada a medias.

Revision ID: f37e7df27a84
Revises: e4237e4b450d
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f37e7df27a84'
down_revision: Union[str, Sequence[str], None] = 'e4237e4b450d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Copias fijas y no las listas de `piezas.py`, como los estados de f429a2e37699:
# una migración describe el esquema de su momento, y si importara las listas
# vivas cambiaría de significado con el código.
FORMATOS = {
    'reel': 'short',
    'video': 'video_largo',
    'post': 'post_individual',
    'carrusel': 'carrusel',
}
PLATAFORMAS = ('instagram', 'tiktok', 'youtube', 'impreso')


def _en_sql(valores) -> str:
    """Una lista literal para `IN`. Sale de las constantes de arriba, nunca
    de lo que haya en la base.
    """
    return ', '.join(f"'{v}'" for v in valores)


def _detener_si_hay(consulta: str, que: str) -> None:
    raros = [str(fila[0]) for fila in op.get_bind().execute(sa.text(consulta))]
    if raros:
        raise RuntimeError(
            f'La migración se detiene: hay {que}: {", ".join(raros)}. '
            'Corrígelo a mano y vuelve a migrar; no se ha cambiado nada.'
        )


def upgrade() -> None:
    """Upgrade schema."""
    _detener_si_hay(
        'SELECT DISTINCT formato FROM pieza WHERE formato IS NOT NULL'
        f' AND formato NOT IN ({_en_sql(FORMATOS)}) ORDER BY formato',
        'formatos que no se sabe convertir',
    )
    _detener_si_hay(
        "SELECT DISTINCT plataforma FROM pieza WHERE btrim(coalesce(plataforma, '')) <> ''"
        f' AND lower(btrim(plataforma)) NOT IN ({_en_sql(PLATAFORMAS)}) ORDER BY plataforma',
        'plataformas que no se sabe convertir',
    )

    op.execute(
        'UPDATE pieza SET formato = CASE formato'
        + ''.join(f" WHEN '{viejo}' THEN '{nuevo}'" for viejo, nuevo in FORMATOS.items())
        + ' END WHERE formato IS NOT NULL'
    )

    op.alter_column(
        'pieza',
        'plataforma',
        existing_type=sa.String(length=50),
        type_=sa.ARRAY(sa.String(length=20)),
        postgresql_using=(
            "CASE WHEN btrim(coalesce(plataforma, '')) = '' THEN '{}'::varchar(20)[]"
            ' ELSE ARRAY[lower(btrim(plataforma))]::varchar(20)[] END'
        ),
        server_default='{}',
        nullable=False,
    )

    op.add_column('pieza', sa.Column('proposito', sa.String(length=20), nullable=True))
    op.add_column('pieza', sa.Column('nivel', sa.String(length=20), nullable=True))
    op.add_column(
        'pieza',
        sa.Column('copy_grafico', sa.ARRAY(sa.Text()), server_default='{}', nullable=False),
    )
    op.add_column(
        'pieza', sa.Column('caption', sa.Text(), server_default='', nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    _detener_si_hay(
        'SELECT id FROM pieza WHERE formato IS NOT NULL'
        f' AND formato NOT IN ({_en_sql(FORMATOS.values())}) ORDER BY id',
        'piezas con un formato que la versión anterior no conoce, como el póster',
    )
    _detener_si_hay(
        'SELECT id FROM pieza WHERE cardinality(plataforma) > 1 ORDER BY id',
        'piezas con más de un destino, y la versión anterior guarda uno',
    )

    op.drop_column('pieza', 'caption')
    op.drop_column('pieza', 'copy_grafico')
    op.drop_column('pieza', 'nivel')
    op.drop_column('pieza', 'proposito')

    # Antes que el tipo, en otra sentencia: el valor por defecto, porque
    # Postgres intentaría convertir también `'{}'` y una lista no pasa a texto;
    # y el `NOT NULL`, porque la lista vacía pasa a nulo.
    op.alter_column(
        'pieza',
        'plataforma',
        existing_type=sa.ARRAY(sa.String(length=20)),
        server_default=None,
        nullable=True,
    )
    op.alter_column(
        'pieza',
        'plataforma',
        existing_type=sa.ARRAY(sa.String(length=20)),
        type_=sa.String(length=50),
        postgresql_using='plataforma[1]',
    )

    op.execute(
        'UPDATE pieza SET formato = CASE formato'
        + ''.join(f" WHEN '{nuevo}' THEN '{viejo}'" for viejo, nuevo in FORMATOS.items())
        + ' END WHERE formato IS NOT NULL'
    )
