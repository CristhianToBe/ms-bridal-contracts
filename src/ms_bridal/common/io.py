"""Funciones de entrada/salida reutilizables para ms_bridal."""

import json
from pathlib import Path
import sys

def load_json(json_path: str) -> dict:
    """
    Carga un archivo JSON y devuelve su contenido como dict.
    Lanza FileNotFoundError si el archivo no existe.
    """
    ruta = Path(json_path)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo JSON: {ruta}")
    with ruta.open("r", encoding="utf-8") as f:
        return json.load(f)

def parse_args(expected_args: int, usage_message: str) -> list[str]:
    """
    Valida argumentos de línea de comandos para scripts tradicionales.
    Devuelve los argumentos (sin incluir el nombre del script).
    """
    if len(sys.argv) != expected_args:
        print(usage_message)
        sys.exit(1)
    return sys.argv[1:]
