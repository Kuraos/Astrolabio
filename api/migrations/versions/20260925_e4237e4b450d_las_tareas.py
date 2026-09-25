"""las tareas

Criterio AD1 de `docs/fase-6-tablero.md`: la checklist de cada pieza y las
tareas sueltas, que son las que no tienen pieza. Quién la marcó y cuándo son
nulos mientras está pendiente: estar hecha es tenerlos.

No es historia, a diferencia de `traspaso`: se marca, se desmarca y se borra,
y por eso no lleva el trigger de solo inserción (§2.6).

Revision ID: e4237e4b450d
Revises: ec6cd77c5b22
Create Date: 2026-09-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4237e4b450d'
down_revision: Union[str, Sequence[str], None] = 'ec6cd77c5b22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'tarea',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pieza_id', sa.Integer(), nullable=True),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('marcada_por', sa.String(length=50), nullable=True),
        sa.Column('marcada_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('creada_por', sa.String(length=50), nullable=False),
        sa.Column(
            'creada_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['pieza_id'], ['pieza.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tarea_pieza_id'), 'tarea', ['pieza_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tarea_pieza_id'), table_name='tarea')
    op.drop_table('tarea')
