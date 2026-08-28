"""la pieza gana guion

Criterio H1. La pieza pasa de tener solo un título a llevar el guion y los
campos que la plantilla del vault pide para el frontmatter.

Los dos campos obligatorios entran con `server_default`: sin él, añadir una
columna `NOT NULL` a una tabla con filas falla, y con él las piezas que ya
existen quedan con guion vacío y sin respaldo, que es exactamente su estado.

**Sigue sin columna `estado`** (CLAUDE.md §2.8): los estados del flujo salen
de una conversación con el editor que todavía no ha ocurrido, y llegarán en
su propia migración cuando ocurra.

Revision ID: 7390a2fd6023
Revises: 7f351fac121b
Create Date: 2026-08-27 04:34:38.204026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7390a2fd6023'
down_revision: Union[str, Sequence[str], None] = '7f351fac121b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'pieza',
        sa.Column('guion', sa.Text(), server_default='', nullable=False),
    )
    op.add_column(
        'pieza', sa.Column('formato', sa.String(length=20), nullable=True)
    )
    op.add_column('pieza', sa.Column('tema', sa.String(length=100), nullable=True))
    op.add_column(
        'pieza', sa.Column('plataforma', sa.String(length=50), nullable=True)
    )
    op.add_column(
        'pieza',
        sa.Column(
            'respaldo',
            sa.ARRAY(sa.String(length=200)),
            server_default='{}',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pieza', 'respaldo')
    op.drop_column('pieza', 'plataforma')
    op.drop_column('pieza', 'tema')
    op.drop_column('pieza', 'formato')
    op.drop_column('pieza', 'guion')
