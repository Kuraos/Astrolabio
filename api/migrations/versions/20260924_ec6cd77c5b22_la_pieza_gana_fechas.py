"""la pieza gana fechas

Criterio AC1 de `docs/fase-6-tablero.md`: la entrega del diseño —la «fecha de
entrega» del editor— y la publicación prevista. `DATE`, sin hora ni zona: son
días del calendario, y un día no se corre al pasar de UTC a Bogotá. Nulas
mientras no se decidan, como están las piezas que ya existen.

Revision ID: ec6cd77c5b22
Revises: 550cb0579c43
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec6cd77c5b22'
down_revision: Union[str, Sequence[str], None] = '550cb0579c43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('pieza', sa.Column('fecha_entrega', sa.Date(), nullable=True))
    op.add_column(
        'pieza', sa.Column('fecha_publicacion_prevista', sa.Date(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pieza', 'fecha_publicacion_prevista')
    op.drop_column('pieza', 'fecha_entrega')
