"""la pieza se archiva

Criterio BD1 de `docs/fase-12-fuentes-y-archivo.md`: una pieza no se borra,
porque su historia es append-only (ADR 0008); se archiva. `archivada_en` es
nula mientras la pieza está en el taller, como todas las que ya existen, y
guarda cuándo salió de él.

Revision ID: 3b9e1c7a52d4
Revises: 8586834f48e9
Create Date: 2026-10-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b9e1c7a52d4'
down_revision: Union[str, Sequence[str], None] = '8586834f48e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'pieza', sa.Column('archivada_en', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pieza', 'archivada_en')
