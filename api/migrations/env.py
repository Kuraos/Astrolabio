"""Entorno de Alembic.

La URL de la base sale de `DATABASE_URL` —la misma que usa la aplicación—, no
de `alembic.ini`: duplicarla en dos sitios es la forma habitual de migrar una
base distinta de la que se sirve. Las pruebas la sustituyen para apuntar a la
base de pruebas.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# `compare_metadata` de las pruebas y `alembic check` comparan contra esto.
target_metadata = Base.metadata


def _url() -> str:
    """La sobreescritura tiene prioridad: es como las pruebas apuntan a su
    propia base sin tocar el entorno del proceso.
    """
    return config.get_main_option("sqlalchemy.url") or settings.database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuracion = config.get_section(config.config_ini_section, {})
    configuracion["sqlalchemy.url"] = _url()

    connectable = engine_from_config(
        configuracion, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Sin esto Alembic ignora los cambios de tipo de columna y una
            # deriva real pasaría desapercibida en `alembic check`.
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
