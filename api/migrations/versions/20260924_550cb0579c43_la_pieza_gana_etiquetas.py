"""la pieza gana etiquetas

Criterio Y2 de `docs/fase-5-temas.md`: etiquetas libres en la pieza, para
saber de qué ha hablado Voz del Cosmos. Una lista en la propia pieza, como
`respaldo`, y vacía por defecto: las piezas que ya existen no tienen ninguna.

El tema no cambia de columna: pasa a lista cerrada en la API (Y1), como ya lo
es el formato.

Revision ID: 550cb0579c43
Revises: 9eb73d51fbe2
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '550cb0579c43'
down_revision: Union[str, Sequence[str], None] = '9eb73d51fbe2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'pieza',
        sa.Column(
            'etiquetas',
            sa.ARRAY(sa.Text()),
            server_default='{}',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pieza', 'etiquetas')
