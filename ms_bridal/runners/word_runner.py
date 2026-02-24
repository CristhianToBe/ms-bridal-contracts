import os
import win32com.client as win32
import pythoncom 

from ms_bridal.common.common_office import load_json, parse_args
from ms_bridal.common.mappers import apply_mappings


def run_word(base_docx: str, data_json: str, mapping_file: str, output_docx: str) -> None:
    """
    Ejecuta todo el flujo de generación del Word.

    :param base_docx: Ruta a la plantilla base (.docx)
    :param data_json: Ruta al JSON con los datos
    :param mapping_file: Ruta al JSON de mapeo
    :param output_docx: Ruta donde se guardará el Word generado
    """

    # Asegurar que las rutas sean absolutas
    base_docx = os.path.abspath(base_docx)
    data_json = os.path.abspath(data_json)
    mapping_file = os.path.abspath(mapping_file)
    output_docx = os.path.abspath(output_docx)

    print(f"📄 Abriendo plantilla Word: {base_docx}")

    data = load_json(data_json)
    mapping_config = load_json(mapping_file)

    # 👇 CLAVE: inicializar COM en este hilo (el del request de Django)
    pythoncom.CoInitialize()
    try:
        try:
            word = win32.Dispatch("Word.Application")
        except AttributeError:
            # Si falla la caché COM, usar Dispatch directamente
            from win32com.client import Dispatch
            word = Dispatch("Word.Application")

        word.Visible = False
        print(f"Intentando abrir plantilla: {base_docx}")
        doc = word.Documents.Open(base_docx)

        # Aplica mapeo desde JSON
        apply_mappings(doc, data, mapping_config)

        # Si el archivo de salida ya existe, lo borramos para evitar conflictos
        if os.path.exists(output_docx):
            os.remove(output_docx)

        doc.SaveAs(output_docx)
        doc.Close(SaveChanges=True)
        word.Quit()
        print(f"✅ Documento Word generado: {output_docx}")

    finally:
        # 👇 Muy importante liberar COM
        pythoncom.CoUninitialize()

def main() -> None:
    """
    Punto de entrada cuando se ejecuta por consola / .bat
    """
    base_docx, data_json, mapping_file, output_docx = parse_args(
        5,
        "Uso: python script_word.py <base_docx> <data_json> <mapping_json> <output_docx>",
    )
    run_word(base_docx, data_json, mapping_file, output_docx)


if __name__ == "__main__":
    main()
