from pathlib import Path
import sys
import os
import io
import zipfile
import uuid
import json

from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.http import require_GET, require_POST

from notion.contracts import create_contract_row
from notion.client import NotionError

from .sync import sync_dresses_from_export, sync_clients_from_contracts_export
from cache.cache_db import list_dresses, list_clients  # <- si NO la tienes, bórrala y quita vestidos/clientes del context


# 👉 AÑADIMOS LA RAÍZ DEL REPO AL PYTHONPATH
# settings.BASE_DIR = carpeta "webui" (donde está manage.py)
WEBUI_BASE = Path(settings.BASE_DIR)          # ...\dossier-builder\webui
REPO_ROOT = WEBUI_BASE.parent                 # ...\dossier-builder

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Scripts
from word.script_word import run_word
from excel.script_excel import run_excel


def save_uploaded_file(file):
    path = default_storage.save(file.name, ContentFile(file.read()))
    return default_storage.path(path)


def resolve_path(path_str: str, base: Path | None = None) -> Path:
    """
    Si la ruta es absoluta, la retorna tal cual.
    Si es relativa, la une a base (por defecto REPO_ROOT).
    """
    if not path_str:
        raise ValueError("resolve_path recibió None/vacío")
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (base or REPO_ROOT) / p


def save_json_from_text(json_text: str, prefix: str) -> str:
    """
    Valida el JSON y lo guarda en un archivo temporal dentro de MEDIA_ROOT.
    Devuelve la ruta absoluta del archivo.
    """
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}")

    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)

    filename = f"{prefix}_{uuid.uuid4().hex}.json"
    path = media_root / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    return str(path)


def index(request):
    # IMPORTANTE: usa una sola carpeta para plantillas.
    # En tu código estabas mezclando Plantillas/plantillas.
    plantillas_dir = REPO_ROOT / "plantillas"
    configs_dir = REPO_ROOT / "configs"

    plantillas_dir.mkdir(parents=True, exist_ok=True)
    configs_dir.mkdir(parents=True, exist_ok=True)

    word_files = sorted(plantillas_dir.glob("*.docx"))
    excel_files = sorted(plantillas_dir.glob("*.xlsx"))
    mapping_files = sorted(configs_dir.glob("*.json"))
    json_base_files = sorted(plantillas_dir.glob("*.json"))

    # Defaults: si existen, perfecto. Si no, deja vacío.
    word_base_default = word_files[0] if word_files else None
    excel_base_default = excel_files[0] if excel_files else None
    word_mapping_default = mapping_files[0] if mapping_files else None
    excel_mapping_default = mapping_files[0] if mapping_files else None

    context = {
        "word_base_default": str(word_base_default.relative_to(REPO_ROOT)) if word_base_default else "",
        "word_mapping_default": str(word_mapping_default.relative_to(REPO_ROOT)) if word_mapping_default else "",
        "word_out_name_default": "Contrato.docx",

        "excel_base_default": str(excel_base_default.relative_to(REPO_ROOT)) if excel_base_default else "",
        "excel_mapping_default": str(excel_mapping_default.relative_to(REPO_ROOT)) if excel_mapping_default else "",
        "excel_out_name_default": "Salida.xlsx",

        "json_base_templates": [{"value": str(p.relative_to(REPO_ROOT)), "name": p.name} for p in json_base_files],
        "word_templates": [{"value": str(p.relative_to(REPO_ROOT)), "name": p.name} for p in word_files],
        "excel_templates": [{"value": str(p.relative_to(REPO_ROOT)), "name": p.name} for p in excel_files],
        "mapping_templates": [{"value": str(p.relative_to(REPO_ROOT)), "name": p.name} for p in mapping_files],

        "word_json_default": "",
        "excel_json_default": "",

        # selects de catálogos (si tienes cache_db)
        "dresses": list_dresses(active_only=False),
        "clients": list_clients(),
    }

    return render(request, "builder/index.html", context)


@require_POST
def refresh_catalogs(request):
    """
    Lee exports locales (JSON) y actualiza cache local.
    """
    # Ajusta rutas a donde realmente estés guardando los exports
    base = REPO_ROOT
    vestidos_path = base / "data" / "notion_exports" / "vestidos.json"
    contratos_path = base / "data" / "notion_exports" / "contratos.json"


    if not vestidos_path.exists():
        return JsonResponse({"ok": False, "error": f"No existe: {vestidos_path}"}, status=400)
    if not contratos_path.exists():
        return JsonResponse({"ok": False, "error": f"No existe: {contratos_path}"}, status=400)

    n1 = sync_dresses_from_export(vestidos_path)
    n2 = sync_clients_from_contracts_export(contratos_path)

    return JsonResponse({"ok": True, "dresses_upserted": n1, "clients_upserted": n2})

@require_POST
def upload_template_view(request):
    """
    Sube una plantilla (Word/Excel) y la guarda en REPO_ROOT/plantillas.
    """
    file = request.FILES.get("template_file")
    if not file:
        return HttpResponse("No se recibió ningún archivo de plantilla.", status=400)

    allowed_exts = {".docx", ".xlsx"}
    suffix = Path(file.name).suffix.lower()
    if suffix not in allowed_exts:
        return HttpResponse("Solo se permiten plantillas .docx o .xlsx.", status=400)

    plantillas_dir = REPO_ROOT / "plantillas"
    plantillas_dir.mkdir(parents=True, exist_ok=True)

    custom_name = (request.POST.get("template_name") or "").strip()
    if custom_name:
        if not custom_name.lower().endswith(suffix):
            custom_name += suffix
        dest_path = plantillas_dir / custom_name
    else:
        dest_path = plantillas_dir / file.name

    with open(dest_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return redirect("index")


@require_POST
def run_word_view(request):
    """
    Genera Word + envía a Notion + descarga ZIP(docx + data.json) + limpia temporales
    """
    #print("POST KEYS:", list(request.POST.keys()))
    
    # Tu index usa name="word_base" y name="mapping_json"
    word_base = (request.POST.get("word_base") or "").strip()
    if not word_base:
        return HttpResponseBadRequest("Falta 'word_base' (Plantilla Word). Revisa el name del <select>.")
    
    mapping_json = (request.POST.get("mapping_json") or "").strip()
    if not mapping_json:
        return HttpResponseBadRequest("Falta 'mapping_json' (Mapping). Revisa el name del <select>.")
    
    try:
        base_docx = resolve_path(word_base, REPO_ROOT)
        mapping_file = resolve_path(mapping_json, REPO_ROOT)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    
    out_name = (request.POST.get("output_name") or "").strip()
    if not out_name:
        return HttpResponseBadRequest("Debes indicar el nombre del archivo Word de salida.")
    if not out_name.lower().endswith(".docx"):
        out_name += ".docx"
    
    outputs_dir = Path(settings.MEDIA_ROOT) / "word_outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_docx = outputs_dir / out_name

    json_text = (request.POST.get("json_text") or "").strip()
    if not json_text:
        return HttpResponse("No se recibió contenido JSON para Word.", status=400)
    #print(json_text)
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as e:
        return HttpResponse(f"JSON inválido: {e}", status=400)
    # Parse payload una vez (para Notion)
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as e:
        return HttpResponse(f"JSON inválido: {e}", status=400)
    
    # Notion (si falla, tú decides si bloquea o no; aquí bloquea)
    try:
        notion_resp = create_contract_row(payload)
        print("✅ Notion page:", notion_resp.get("id"))
    except NotionError as e:
        return HttpResponse(f"Falló envío a Notion: {e}", status=500)

    # Guardar JSON temporal
    try:
        data_json_path = save_json_from_text(json_text, "word")
    except ValueError as e:
        return HttpResponse(str(e), status=400)

    # Generar Word
    run_word(
        str(base_docx),
        data_json_path,
        str(mapping_file),
        str(output_docx),
    )

    if not output_docx.exists():
        return HttpResponse("Se ejecutó la generación, pero no se encontró el archivo de salida.", status=500)

    # ZIP en memoria (docx + data.json)
    zip_buffer = io.BytesIO()
    zip_name = f"{output_docx.stem}_paquete.zip"

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_docx, arcname=output_docx.name)
            zf.write(data_json_path, arcname="data.json")
        zip_buffer.seek(0)
    finally:
        # limpiar temporales
        try:
            if output_docx.exists():
                os.remove(output_docx)
        except OSError:
            pass
        try:
            tmp_json = Path(data_json_path)
            if tmp_json.exists():
                os.remove(tmp_json)
        except OSError:
            pass

    return FileResponse(zip_buffer, as_attachment=True, filename=zip_name)


@require_POST
def run_excel_view(request):
    """
    Genera Excel + descarga ZIP(xlsx + data.json) + limpia temporales
    """
    # Para coherencia con tu index, lo normal es:
    # name="excel_base", name="mapping_json" o name="excel_mapping"
    excel_base = (request.POST.get("excel_base") or "").strip()
    if not excel_base:
        return HttpResponseBadRequest("Falta 'excel_base' (Plantilla Excel).")

    # Si tu select usa mapping_json también, reutilízalo:
    excel_mapping = (request.POST.get("excel_mapping") or request.POST.get("mapping_json") or "").strip()
    if not excel_mapping:
        return HttpResponseBadRequest("Falta mapping para Excel (excel_mapping o mapping_json).")

    try:
        base_excel = resolve_path(excel_base, REPO_ROOT)
        mapping_file = resolve_path(excel_mapping, REPO_ROOT)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

    out_name = (request.POST.get("excel_out_name") or request.POST.get("output_name") or "").strip()
    if not out_name:
        return HttpResponse("Debes indicar el nombre del archivo Excel de salida.", status=400)
    if not out_name.lower().endswith(".xlsx"):
        out_name += ".xlsx"

    outputs_dir = Path(settings.MEDIA_ROOT) / "excel_outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    output_excel = outputs_dir / out_name

    json_text = (request.POST.get("excel_json_text") or request.POST.get("json_text") or "").strip()
    if not json_text:
        return HttpResponse("No se recibió contenido JSON para Excel.", status=400)

    try:
        data_json_path = save_json_from_text(json_text, "excel")
    except ValueError as e:
        return HttpResponse(str(e), status=400)

    run_excel(
        str(base_excel),
        data_json_path,
        str(mapping_file),
        str(output_excel),
    )

    if not output_excel.exists():
        return HttpResponse("Se ejecutó la generación, pero no se encontró el archivo de salida.", status=500)

    zip_buffer = io.BytesIO()
    zip_name = f"{output_excel.stem}_paquete.zip"

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_excel, arcname=output_excel.name)
            zf.write(data_json_path, arcname="data.json")
        zip_buffer.seek(0)
    finally:
        try:
            if output_excel.exists():
                os.remove(output_excel)
        except OSError:
            pass
        try:
            tmp_json = Path(data_json_path)
            if tmp_json.exists():
                os.remove(tmp_json)
        except OSError:
            pass

    return FileResponse(zip_buffer, as_attachment=True, filename=zip_name)


def _blank_leaves(obj):
    """
    Devuelve una copia del objeto donde todos los valores hoja se reemplazan por "".
    Mantiene la estructura (dicts/listas) intacta.
    """
    if isinstance(obj, dict):
        return {k: _blank_leaves(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_blank_leaves(v) for v in obj]
    return ""


@require_POST
def create_json_view(request):
    """
    Recibe el JSON ya editado (como texto) desde el formulario y lo devuelve como archivo descargable.
    """
    json_text = (request.POST.get("json_text") or "").strip()
    if not json_text:
        return HttpResponse("No se recibió JSON para generar.", status=400)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return HttpResponse(f"JSON inválido: {e}", status=400)

    out_name = (request.POST.get("json_out_name") or "").strip() or "data_blank.json"
    if not out_name.lower().endswith(".json"):
        out_name += ".json"

    buffer = io.BytesIO()
    buffer.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=out_name, content_type="application/json")


@require_GET
def get_json_template_view(request):
    """
    Devuelve el JSON base (con todas las hojas en blanco) para usarlo en el editor de la sección de creación.
    """
    template_rel = (request.GET.get("json_template") or "").strip()
    if not template_rel:
        return JsonResponse({"error": "No se recibió json_template."}, status=400)

    template_path = resolve_path(template_rel, REPO_ROOT)
    if not template_path.exists():
        return JsonResponse({"error": "El JSON base no existe."}, status=404)

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            base_data = json.load(f)
    except Exception as e:
        return JsonResponse({"error": f"No se pudo leer el JSON base: {e}"}, status=500)

    blank_data = _blank_leaves(base_data)
    return JsonResponse(blank_data, safe=False)


@require_POST
def create_mapping_view(request):
    """
    Recibe un JSON de mapping ya armado desde el front y lo guarda en configs/,
    devolviéndolo además como descarga.
    """
    mapping_text = (request.POST.get("mapping_text") or "").strip()
    mapping_name = (request.POST.get("mapping_name") or "").strip()

    if not mapping_text:
        return HttpResponse("No se recibió contenido de mapping.", status=400)

    try:
        mapping_data = json.loads(mapping_text)
    except json.JSONDecodeError as e:
        return HttpResponse(f"Mapping JSON inválido: {e}", status=400)

    if not mapping_name:
        mapping_name = "mapping.json"
    if not mapping_name.lower().endswith(".json"):
        mapping_name += ".json"

    configs_dir = REPO_ROOT / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    file_path = configs_dir / mapping_name

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(mapping_data, f, ensure_ascii=False, indent=2)

    buffer = io.BytesIO()
    buffer.write(json.dumps(mapping_data, ensure_ascii=False, indent=2).encode("utf-8"))
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=mapping_name, content_type="application/json")
