"""Configuración de la API, leída del entorno.

Sin valores por defecto (CLAUDE.md §4): si falta `DATABASE_URL`, la aplicación
falla al arrancar con un error claro, que es mucho mejor que arrancar apuntando
a una base que no es la que se creía.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # `extra="ignore"` porque el entorno del contenedor trae más variables de
    # las que esta fase usa; declararlas aquí sería construir la fase
    # siguiente (CLAUDE.md §6).
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str

    # Lo usa la sonda del criterio A4 para emitir la cookie con los mismos
    # atributos que tendrá la sesión real. En HTTP plano sobre Tailscale va en
    # false; pasa a true solo con HTTPS (variante C del ADR 0002).
    cookie_secure: bool = False

    # Criterio B1: las contraseñas de la siembra salen del entorno, nunca del
    # código. Sin valor por defecto las cuatro: una contraseña por defecto en
    # el código es una cuenta abierta en cualquier despliegue que la olvide.
    seed_investigador_user: str
    seed_investigador_password: str
    seed_editor_user: str
    seed_editor_password: str


settings = Settings()
