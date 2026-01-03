import os
import shutil
import pythoncom
import win32com.client as win32

from common.common_office import load_json, parse_args
from common.mappers import apply_mappings


def run_excel(base_excel: str, data_json: str, mapping_file: str, output_excel: str) -> None:
    """
    Ejecuta el flujo de generación del Excel.

    :param base_excel: Ruta a la plantilla base (.xlsx)
    :param data_json: Ruta al JSON con los datos
    :param mapping_file: Ruta al JSON de mapeo
    :param output_excel: Ruta donde se guardará el Excel generado
    """

    # Asegurar rutas absolutas
    base_excel = os.path.abspath(base_excel)
    data_json = os.path.abspath(data_json)
    mapping_file = os.path.abspath(mapping_file)
    output_excel = os.path.abspath(output_excel)

    print(f"📊 Abriendo plantilla Excel: {base_excel}")

    data = load_json(data_json)
    mapping_config = load_json(mapping_file)

    # Copiar plantilla a salida (como ya hacías)
    shutil.copy(base_excel, output_excel)

    pythoncom.CoInitialize()
    try:
        # Puedes usar DispatchEx como tenías, o Dispatch normal
        try:
            excel = win32.DispatchEx("Excel.Application")
        except AttributeError:
            from win32com.client import DispatchEx
            excel = DispatchEx("Excel.Application")

        print(">>> Excel version:", excel.Version)
        excel.Visible = False  # si quieres ver Excel, pon True

        wb = excel.Workbooks.Open(output_excel)

        # Hoja configurable desde el mapping: puede ser índice (1, 2, ...) o nombre ("Hoja1")
        sheet_name = mapping_config.get("sheet", 1)
        sheet = wb.Sheets(sheet_name)

        # Aplica mapeo desde JSON (incluyendo reglas especiales como __TODAY__)
        apply_mappings(sheet, data, mapping_config)

        wb.Save()
        wb.Close(SaveChanges=True)
        excel.Quit()
        print(f"✅ Excel actualizado: {output_excel}")
    finally:
        pythoncom.CoUninitialize()


def main() -> None:
    """
    Punto de entrada CLI / .bat, mantiene compatibilidad con lo que ya tenías.
    """
    base_excel, data_json, mapping_file, output_excel = parse_args(
        5,
        "Uso: python script_excel.py <base_excel> <data_json> <mapping_json> <output_excel>",
    )
    run_excel(base_excel, data_json, mapping_file, output_excel)


if __name__ == "__main__":
    main()
