"""Criterio B4 — las contraseñas se guardan con Argon2id.

Estas pruebas afirman propiedades del formato almacenado, no del texto que
entra. Es la única capa donde un fallo no se ve mirando la pantalla: una
aplicación con las contraseñas en MD5 se comporta exactamente igual que una
correcta hasta el día en que se filtra la base.
"""

from app.security import hash_password, verify_password


def test_el_hash_declara_argon2id():
    """Argon2i y Argon2d también existen y no son intercambiables: `id` es la
    variante híbrida, la única que resiste a la vez canales laterales y
    ataques con GPU. B4 la pide por nombre, así que se comprueba por nombre.
    """
    assert hash_password("nubes-de-magallanes").startswith("$argon2id$")


def test_la_misma_contrasena_produce_hashes_distintos():
    """Sal aleatoria por hash. Sin ella, dos usuarios que eligen la misma
    contraseña quedan con la misma fila, y la base revela que la comparten.
    """
    assert hash_password("misma") != hash_password("misma")


def test_acepta_la_contrasena_correcta():
    almacenado = hash_password("nubes-de-magallanes")

    assert verify_password(almacenado, "nubes-de-magallanes") is True


def test_rechaza_la_contrasena_incorrecta():
    almacenado = hash_password("nubes-de-magallanes")

    assert verify_password(almacenado, "otra-cosa") is False


def test_un_hash_corrupto_no_revienta():
    """La verificación devuelve False ante basura en vez de propagar una
    excepción: si no, una fila dañada convierte un 401 en un 500 y filtra
    que esa cuenta existe.
    """
    assert verify_password("no-soy-un-hash", "lo-que-sea") is False
