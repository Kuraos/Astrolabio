"""la pieza gana enlaces

Criterio P1 de `docs/fase-3-material.md`: los enlaces de referencia de cada
pieza, que hoy van por chat. Una tabla nueva y nada más: las imágenes no entran
en la base (§2.2), viven en la carpeta de la pieza en Syncthing (ADR 0010).

A diferencia de `traspaso`, no es historia: los enlaces se quitan, así que no
lleva el trigger de append-only.

Revision ID: 9eb73d51fbe2
Revises: f429a2e37699
Create Date: 2026-09-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9eb73d51fbe2'
down_revision: Union[str, Sequence[str], None] = 'f429a2e37699'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'enlace',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pieza_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('nota', sa.Text(), nullable=True),
        sa.Column('creado_por', sa.String(length=50), nullable=False),
        sa.Column(
            'creado_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['pieza_id'], ['pieza.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_enlace_pieza_id'), 'enlace', ['pieza_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_enlace_pieza_id'), table_name='enlace')
    op.drop_table('enlace')
