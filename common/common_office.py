import json
import os
from pathlib import Path
import sys

def load_json(json_path):
    """Carga un archivo JSON y retorna el dict."""
    ruta = Path(json_path)   # Maneja acentos y backslashes
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo JSON: {ruta}")
    with ruta.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args(expected_args, usage_message):
    """
    Valida argumentos de línea de comandos.
    expected_args: número esperado (incluyendo script).
    Retorna lista con los argumentos.
    """
    if len(sys.argv) != expected_args:
        print(usage_message)
        sys.exit(1)
    return sys.argv[1:]
