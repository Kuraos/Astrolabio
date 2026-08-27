"""Hashing de contraseñas (criterio B4).

`PasswordHasher` usa Argon2id por defecto y trae los parámetros de coste
recomendados por los autores. No se tocan: elegir a mano el coste en memoria
y el paralelismo es la forma habitual de debilitar Argon2 creyendo afinarlo.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    """Devuelve el hash con sal aleatoria y los parámetros dentro."""
    return _hasher.hash(plain)


def verify_password(stored: str, plain: str) -> bool:
    """Compara sin propagar excepciones.

    Se capturan dos ramas distintas de la jerarquía: `VerificationError` (la
    contraseña no coincide) y `InvalidHashError`, que hereda de `ValueError`
    y salta cuando lo almacenado no es un hash válido. Sin la segunda, una
    fila dañada devolvería 500 en vez de 401 — y un 500 solo en las cuentas
    que existen delata cuáles existen.
    """
    try:
        return _hasher.verify(stored, plain)
    except (VerificationError, InvalidHashError):
        return False
