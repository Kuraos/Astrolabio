"""los bocetos

Criterio AU1 de `docs/fase-9-bocetos.md`: cada boceto pedido a Claude que
llegó a tener respuesta, válido o no, con quién lo pidió, el modelo, la
rejilla, el copy con que se hizo y los tokens que costó (ADR 0016).

`ck_boceto_laminas_o_error` va a mano, como `ck_pieza_estado`: autogenerate
no escribe restricciones CHECK. Un boceto guarda sus láminas o su error,
nunca los dos ni ninguno.

Revision ID: 8586834f48e9
Revises: f37e7df27a84
Create Date: 2026-09-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8586834f48e9'
down_revision: Union[str, Sequence[str], None] = 'f37e7df27a84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'boceto',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pieza_id', sa.Integer(), nullable=False),
        sa.Column('creado_por', sa.String(length=50), nullable=False),
        sa.Column(
            'creado_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('modelo', sa.String(length=100), nullable=False),
        sa.Column('columnas', sa.Integer(), nullable=False),
        sa.Column('filas', sa.Integer(), nullable=False),
        sa.Column('copy_grafico', sa.ARRAY(sa.Text()), nullable=False),
        sa.Column('laminas', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('avisos', sa.ARRAY(sa.Text()), server_default='{}', nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('tokens_entrada', sa.Integer(), nullable=False),
        sa.Column('tokens_salida', sa.Integer(), nullable=False),
        sa.CheckConstraint(
            '(laminas IS NULL) <> (error IS NULL)', name='ck_boceto_laminas_o_error'
        ),
        sa.ForeignKeyConstraint(['pieza_id'], ['pieza.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_boceto_pieza_id'), 'boceto', ['pieza_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_boceto_pieza_id'), table_name='boceto')
    op.drop_table('boceto')
