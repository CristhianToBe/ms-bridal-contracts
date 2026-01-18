# ms_bridal_refactor

Este repositorio contiene una versión refactorizada del proyecto original **ms-bridal-contracts**.

El objetivo es separar responsabilidades, tener un punto de entrada claro y centralizar la configuración. 

## Uso rápido

Instala las dependencias (pendiente definir en `pyproject.toml`) y ejecuta los comandos desde la raíz:

```
python -m ms_bridal.cli generar-word --template plantilla.docx --data datos.json --mapping mapping.json --output contrato.docx
python -m ms_bridal.cli generar-excel --template plantilla.xlsx --data datos.json --mapping mapping.json --output contrato.xlsx
```

## Estructura

La lógica principal vive en el paquete `ms_bridal` dentro de `src/`. Los scripts de Word y Excel se han extraído a `documents/word` y `documents/excel` respectivamente. Las utilidades comunes (carga de JSON, mappers, etc.) están en `common/`.