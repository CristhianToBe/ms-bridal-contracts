from ms_bridal.runners.excel_runner import run_excel
from ms_bridal.runners.word_runner import run_word


def build_word(base_docx: str, data_json: str, mapping_file: str, output_docx: str) -> None:
    run_word(base_docx, data_json, mapping_file, output_docx)


def build_excel(base_excel: str, data_json: str, mapping_file: str, output_excel: str) -> None:
    run_excel(base_excel, data_json, mapping_file, output_excel)
