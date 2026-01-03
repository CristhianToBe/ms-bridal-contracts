"""
Paquete common

Incluye módulos reutilizables para los scripts de Word y Excel:
- common_office: utilidades de carga de JSON y manejo de argumentos
- mappers: aplicación de mapeos dinámicos desde JSON a Word/Excel
"""

# Importaciones rápidas (opcional, para usar directamente desde common)
from .common_office import load_json, parse_args
from .mappers import apply_mappings, get_value_from_path, handle_special
