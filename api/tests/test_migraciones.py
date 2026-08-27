"""Criterio F2 — las migraciones y los modelos no se separan.

Esta es la prueba que justifica Alembic. Sin ella, alguien añade un campo a un
modelo, `create_all` se lo crea en su portátil, todo funciona, y el despliegue
descubre la columna que falta. El fallo aparece lejos de la causa.

`alembic check` compara el esquema que producen las migraciones contra el que
declaran los modelos. Si divergen, esta prueba falla aquí y no en producción.
"""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.models import Base


def test_las_migraciones_producen_el_esquema_de_los_modelos(
    engine_de_prueba, config_alembic
):
    """No queda ninguna diferencia que autogenerate quisiera escribir."""
    command.upgrade(config_alembic, "head")

    with engine_de_prueba.connect() as conexion:
        contexto = MigrationContext.configure(conexion)
        diferencias = compare_metadata(contexto, Base.metadata)

    assert diferencias == [], (
        "Los modelos y las migraciones divergen. Genera la migración que falta:\n"
        "  docker compose run --rm api alembic revision --autogenerate -m '...'"
    )


def test_upgrade_crea_todas_las_tablas_desde_cero(engine_de_prueba, config_alembic):
    """F2 en su forma más literal: base vacía → `upgrade head` → el esquema."""
    command.downgrade(config_alembic, "base")

    assert inspect(engine_de_prueba).get_table_names() == ["alembic_version"] or (
        inspect(engine_de_prueba).get_table_names() == []
    )

    command.upgrade(config_alembic, "head")

    tablas = set(inspect(engine_de_prueba).get_table_names())
    assert {"usuario", "sesion", "pieza"} <= tablas


def test_el_esquema_ya_no_se_crea_con_create_all():
    """F1: ninguna ruta de la aplicación llama a `create_all`.

    Si vuelve, las dos formas de crear el esquema coexisten y cuál gana depende
    del orden de arranque — exactamente la clase de fallo que Alembic elimina.

    Se busca la **llamada** con el árbol sintáctico, no la cadena de texto: un
    comentario que explique por qué no hay `create_all` es documentación útil y
    no puede hacer fallar la prueba que vigila su ausencia.
    """
    import ast
    from pathlib import Path

    culpables = []
    for archivo in (Path(__file__).resolve().parent.parent / "app").rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if (
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "create_all"
            ):
                culpables.append(f"{archivo.name}:{nodo.lineno}")

    assert culpables == []
