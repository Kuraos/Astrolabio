"""la pieza gana estado y traspaso

Criterios K1, K2, M1 y M2 de `docs/fase-2-traspaso.md`. Llega cuando lo
anunciaban las dos migraciones anteriores: después de la conversación con el
editor que pide el §2.8, escrita en `docs/estados-del-flujo.md`.

`estado` entra con `server_default`, así que las piezas que ya existen quedan
en `investigacion`, que es donde están: en manos de Johan.

Dos cosas que autogenerate no escribe, y por eso van a mano:

- `ck_pieza_estado`, la restricción que obliga a pasar por una migración para
  añadir un estado. Autogenerate no ve restricciones CHECK sobre tablas que ya
  existen.
- El trigger que hace append-only a `traspaso` por la base y no por disciplina
  (ADR 0008). Es por sentencia porque `TRUNCATE` solo admite triggers por
  sentencia, y así una sola regla cubre las tres operaciones. La función no
  nombra la tabla: cuando lleguen `snapshot` y `version_pieza`, su migración
  engancha la misma.

Revision ID: f429a2e37699
Revises: 7390a2fd6023
Create Date: 2026-09-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f429a2e37699'
down_revision: Union[str, Sequence[str], None] = '7390a2fd6023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Copia fija y no `app.models.ESTADOS`: una migración describe el esquema de su
# momento, y si importara la lista viva cambiaría de significado con el código.
# Que las dos coincidan lo vigila `test_la_base_admite_esos_estados_y_ninguno_mas`.
ESTADOS = (
    'investigacion',
    'solicitud_entregada',
    'material_aprobado',
    'finalizada',
    'diseno_aprobado',
    'publicada',
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'pieza',
        sa.Column(
            'estado',
            sa.String(length=30),
            server_default='investigacion',
            nullable=False,
        ),
    )
    op.create_check_constraint(
        'ck_pieza_estado',
        'pieza',
        'estado IN ({})'.format(', '.join(f"'{e}'" for e in ESTADOS)),
    )

    op.create_table(
        'traspaso',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pieza_id', sa.Integer(), nullable=False),
        sa.Column('transicion', sa.String(length=30), nullable=False),
        sa.Column('desde', sa.String(length=30), nullable=False),
        sa.Column('hacia', sa.String(length=30), nullable=False),
        sa.Column('creado_por', sa.String(length=50), nullable=False),
        sa.Column(
            'creado_en',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('nota', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['pieza_id'], ['pieza.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_traspaso_pieza_id'), 'traspaso', ['pieza_id'], unique=False
    )

    # `USING MESSAGE` y no `RAISE '% …'`: el `%` pasaría por el escape de
    # parámetros de SQLAlchemy y del driver antes de llegar a PL/pgSQL.
    op.execute(
        """
        CREATE FUNCTION rechazar_cambios_en_historia() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION USING MESSAGE = TG_TABLE_NAME
                || ' es append-only: se inserta, nunca se actualiza ni se borra'
                || ' (ADR 0008)';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER traspaso_append_only
            BEFORE UPDATE OR DELETE OR TRUNCATE ON traspaso
            FOR EACH STATEMENT EXECUTE FUNCTION rechazar_cambios_en_historia()
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP TRIGGER traspaso_append_only ON traspaso')
    op.execute('DROP FUNCTION rechazar_cambios_en_historia()')
    op.drop_index(op.f('ix_traspaso_pieza_id'), table_name='traspaso')
    op.drop_table('traspaso')
    op.drop_constraint('ck_pieza_estado', 'pieza', type_='check')
    op.drop_column('pieza', 'estado')
