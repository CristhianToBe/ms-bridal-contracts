import argparse
from ms_bridal.documents.word.renderer import run_word
from ms_bridal.documents.excel.exporter import run_excel

def main() -> None:
    """
    Punto de entrada para la CLI del proyecto.
    Soporta subcomandos para generar documentos Word y Excel.
    """
    parser = argparse.ArgumentParser(prog="ms-bridal", description="CLI para ms_bridal")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comando para generar Word
    parser_word = subparsers.add_parser("generar-word", help="Genera un contrato en formato .docx")
    parser_word.add_argument("--template", required=True, help="Ruta a la plantilla Word .docx")
    parser_word.add_argument("--data", required=True, help="Ruta al JSON con los datos")
    parser_word.add_argument("--mapping", required=True, help="Ruta al JSON de mapeo")
    parser_word.add_argument("--output", required=True, help="Ruta de salida del archivo .docx")

    # Comando para generar Excel
    parser_excel = subparsers.add_parser("generar-excel", help="Genera un contrato en formato .xlsx")
    parser_excel.add_argument("--template", required=True, help="Ruta a la plantilla Excel .xlsx")
    parser_excel.add_argument("--data", required=True, help="Ruta al JSON con los datos")
    parser_excel.add_argument("--mapping", required=True, help="Ruta al JSON de mapeo")
    parser_excel.add_argument("--output", required=True, help="Ruta de salida del archivo .xlsx")

    args = parser.parse_args()

    if args.command == "generar-word":
        run_word(args.template, args.data, args.mapping, args.output)
    elif args.command == "generar-excel":
        run_excel(args.template, args.data, args.mapping, args.output)
    else:
        parser.print_help()
