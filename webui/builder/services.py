import io
import json
import os
import uuid
import zipfile
from pathlib import Path
import sys

from django.conf import settings

WEBUI_BASE = Path(settings.BASE_DIR)
REPO_ROOT = WEBUI_BASE.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from excel.script_excel import run_excel
from notion.contracts import create_contract_row as notion_create_contract_row
from word.script_word import run_word


class JsonService:
    @staticmethod
    def parse_and_store_temp_json(json_text: str, prefix: str) -> tuple[dict, str]:
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as error:
            raise ValueError(f"JSON inválido: {error}") from error

        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_{uuid.uuid4().hex}.json"
        json_path = media_root / filename

        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, ensure_ascii=False, indent=2)

        return payload, str(json_path)


class ZipService:
    @staticmethod
    def build_package(document_path: Path, json_path: str) -> tuple[io.BytesIO, str]:
        zip_buffer = io.BytesIO()
        zip_name = f"{document_path.stem}_paquete.zip"

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(document_path, arcname=document_path.name)
            zip_file.write(json_path, arcname="data.json")

        zip_buffer.seek(0)
        return zip_buffer, zip_name


class DocumentService:
    @staticmethod
    def generate_word_package(base_docx: Path, mapping_file: Path, output_docx: Path, json_text: str) -> tuple[io.BytesIO, str]:
        _, data_json_path = JsonService.parse_and_store_temp_json(json_text, "word")

        try:
            run_word(
                str(base_docx),
                data_json_path,
                str(mapping_file),
                str(output_docx),
            )

            if not output_docx.exists():
                raise RuntimeError("Se ejecutó la generación, pero no se encontró el archivo de salida.")

            return ZipService.build_package(output_docx, data_json_path)
        finally:
            if output_docx.exists():
                os.remove(output_docx)

            tmp_json = Path(data_json_path)
            if tmp_json.exists():
                os.remove(tmp_json)

    @staticmethod
    def generate_excel_package(base_excel: Path, mapping_file: Path, output_excel: Path, json_text: str) -> tuple[io.BytesIO, str]:
        _, data_json_path = JsonService.parse_and_store_temp_json(json_text, "excel")

        try:
            run_excel(
                str(base_excel),
                data_json_path,
                str(mapping_file),
                str(output_excel),
            )

            if not output_excel.exists():
                raise RuntimeError("Se ejecutó la generación, pero no se encontró el archivo de salida.")

            return ZipService.build_package(output_excel, data_json_path)
        finally:
            if output_excel.exists():
                os.remove(output_excel)

            tmp_json = Path(data_json_path)
            if tmp_json.exists():
                os.remove(tmp_json)


class NotionService:
    @staticmethod
    def create_contract_row(payload: dict) -> dict:
        return notion_create_contract_row(payload)
