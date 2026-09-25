"""ADR 0013 — la imagen instala exactamente el lock.

`pip install -c constraints.txt` impide que una transitiva se mueva, pero no
que entre una dependencia sin fijar: si `requirements.txt` gana un paquete y
nadie regenera el lock, pip lo instala suelto y sin avisar. Pillow, en la
Fase 3, entraría así. Esta prueba lo descubre aquí y no meses después.
"""

import subprocess
import sys
from pathlib import Path

_LOCK = Path(__file__).resolve().parent.parent / "constraints.txt"


def test_la_imagen_instala_exactamente_el_lock():
    """`pip freeze` dentro de la imagen y el lock son el mismo conjunto: ni un
    paquete suelto ni una línea que ya no se instala.
    """
    instalado = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    fijado = [
        linea
        for linea in _LOCK.read_text(encoding="utf-8").splitlines()
        if linea and not linea.startswith("#")
    ]

    assert set(instalado) == set(fijado), (
        "La imagen y constraints.txt divergen. Regenera el lock:\n"
        "  docker build --no-cache --target lock --output api api"
    )
