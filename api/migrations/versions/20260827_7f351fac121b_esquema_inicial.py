"""esquema inicial

Estado del esquema al cerrar la Fase 0: `usuario`, `sesion` y `pieza`.
Generada con `--autogenerate` contra una base limpia, no escrita a mano.

`pieza` no tiene columna `estado`, y no es un olvido: los estados del flujo
salen de una conversación con el editor que todavía no ha ocurrido
(CLAUDE.md §2.8). Cuando ocurra, llegarán en su propia migración.

Revision ID: 7f351fac121b
Revises:
Create Date: 2026-08-27 04:15:00.860545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f351fac121b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'pieza',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column(
            'creada_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('creada_por', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'usuario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario', sa.String(length=50), nullable=False),
        sa.Column('hash_password', sa.String(length=255), nullable=False),
        sa.Column('rol', sa.String(length=20), nullable=False),
        sa.Column(
            'creado_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_usuario_usuario'), 'usuario', ['usuario'], unique=True)
    op.create_table(
        'sesion',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column(
            'creada_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('expira_en', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_sesion_usuario_id'), 'sesion', ['usuario_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sesion_usuario_id'), table_name='sesion')
    op.drop_table('sesion')
    op.drop_index(op.f('ix_usuario_usuario'), table_name='usuario')
    op.drop_table('usuario')
    op.drop_table('pieza')
