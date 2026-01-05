import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from cache.cache_db import upsert_dresses, upsert_clients


def _safe_get(obj: Any, path: List[Any], default=None):
    """
    Navega dict/list de forma segura.
    path puede incluir strings (dict keys) o ints (list index).
    """
    cur = obj
    for p in path:
        if cur is None:
            return default
        if isinstance(p, int):
            if not isinstance(cur, list) or p < 0 or p >= len(cur):
                return default
            cur = cur[p]
        else:
            if not isinstance(cur, dict) or p not in cur:
                return default
            cur = cur[p]
    return cur


def _first_nonempty(*vals: Any, default="") -> Any:
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        return v
    return default


def _notion_title(props: Dict[str, Any], key_candidates: List[str]) -> str:
    """
    Lee una propiedad tipo Title: props[KEY]["title"][0]["text"]["content"] o plain_text
    """
    for k in key_candidates:
        title0 = _safe_get(props, [k, "title", 0], None)
        if isinstance(title0, dict):
            v = _first_nonempty(
                _safe_get(title0, ["text", "content"], ""),
                _safe_get(title0, ["plain_text"], ""),
                default=""
            )
            if v:
                return str(v).strip()
    return ""


def _notion_rich_text(props: Dict[str, Any], key_candidates: List[str]) -> str:
    """
    Lee una propiedad tipo rich_text: props[KEY]["rich_text"][0]["text"]["content"] o plain_text
    """
    for k in key_candidates:
        rt0 = _safe_get(props, [k, "rich_text", 0], None)
        if isinstance(rt0, dict):
            v = _first_nonempty(
                _safe_get(rt0, ["text", "content"], ""),
                _safe_get(rt0, ["plain_text"], ""),
                default=""
            )
            if v:
                return str(v).strip()
    return ""


def _notion_select(props: Dict[str, Any], key_candidates: List[str]) -> str:
    """
    Lee select: props[KEY]["select"]["name"] o status: props[KEY]["status"]["name"]
    """
    for k in key_candidates:
        v = _safe_get(props, [k, "select", "name"], None)
        if v:
            return str(v).strip()
        v = _safe_get(props, [k, "status", "name"], None)
        if v:
            return str(v).strip()
    return ""


def _notion_phone(props: Dict[str, Any], key_candidates: List[str]) -> str:
    for k in key_candidates:
        v = _safe_get(props, [k, "phone_number"], None)
        if v:
            return str(v).strip()
    return ""


# -----------------------------
# SYNC DRESSES
# -----------------------------
def sync_dresses_from_export(export_path: Path) -> int:
    """
    Lee un export JSON de Notion (o lista) y llena cache SQLite (tabla dresses).

    Intenta mapear:
    - page_id = page["id"]
    - name: desde "Nombre"/"Name"/"Vestido"/etc (title)
    - reference: desde "Referencia"/"Ref"/etc (rich_text o title)
    - status: desde "Estatus"/"Status"/etc (select/status)
    """
    raw = json.loads(export_path.read_text(encoding="utf-8"))
    pages = raw.get("results") if isinstance(raw, dict) else raw
    if not isinstance(pages, list):
        raise ValueError("Formato inesperado en export de vestidos (se esperaba 'results' o lista).")

    rows: List[Dict[str, Any]] = []

    for page in pages:
        if not isinstance(page, dict):
            continue

        page_id = (page.get("id") or "").strip()
        if not page_id:
            continue

        props = page.get("properties") or {}
        if not isinstance(props, dict):
            props = {}

        name = _notion_title(props, ["Nombre", "Name", "Vestido", "Título", "Title"])
        # referencia puede venir como rich_text o title dependiendo de tu DB
        reference = _first_nonempty(
            _notion_rich_text(props, ["Referencia", "Ref", "Referencia Vestido", "Modelo"]),
            _notion_title(props, ["Referencia", "Ref", "Referencia Vestido", "Modelo"]),
            default=""
        )
        status = _notion_select(props, ["Estatus", "Status", "Estado"])

        # fallback: si no hay name, intenta con "plain_text" de cualquier title del primer property title
        if not name:
            # intentar encontrar "cualquier" propiedad title
            for k, v in props.items():
                if isinstance(v, dict) and isinstance(v.get("title"), list) and v["title"]:
                    name = _first_nonempty(
                        _safe_get(v, ["title", 0, "plain_text"], ""),
                        _safe_get(v, ["title", 0, "text", "content"], ""),
                        default=""
                    ).strip()
                    if name:
                        break

        if not name:
            # si aún no, lo dejamos pero con algo mínimo
            name = f"(Sin nombre) {page_id[:8]}"

        rows.append(
            {"page_id": page_id, "name": name, "reference": reference, "status": status}
        )

    return upsert_dresses(rows)


# -----------------------------
# SYNC CLIENTS (DERIVADOS DE CONTRATOS)
# -----------------------------
def sync_clients_from_contracts_export(export_path: Path) -> int:
    """
    Deriva clientes desde el export de contratos en Notion y llena cache SQLite (tabla clients).

    Busca:
    - "Nombre Cliente" (rich_text)
    - "Dirección" (rich_text)
    - "Teléfono 1" (phone_number)
    - "Teléfono 2" (phone_number)

    client_key:
    - por defecto: "NOMBRE|TEL1" si hay tel1, si no: "NOMBRE"
    """
    raw = json.loads(export_path.read_text(encoding="utf-8"))
    pages = raw.get("results") if isinstance(raw, dict) else raw
    if not isinstance(pages, list):
        raise ValueError("Formato inesperado en export de contratos (se esperaba 'results' o lista).")

    rows: List[Dict[str, Any]] = []

    for page in pages:
        if not isinstance(page, dict):
            continue
        props = page.get("properties") or {}
        if not isinstance(props, dict):
            continue

        nombre = _first_nonempty(
            _notion_rich_text(props, ["Nombre Cliente", "Cliente", "Nombre"]),
            _notion_title(props, ["Nombre Cliente", "Cliente", "Nombre"]),
            default=""
        ).strip()

        if not nombre:
            continue

        direccion = _first_nonempty(
            _notion_rich_text(props, ["Dirección", "Direccion", "Address"]),
            default=""
        ).strip()

        tel1 = _notion_phone(props, ["Teléfono 1", "Telefono 1", "Phone 1", "Tel1"])
        tel2 = _notion_phone(props, ["Teléfono 2", "Telefono 2", "Phone 2", "Tel2"])

        client_key = f"{nombre}|{tel1}" if tel1 else nombre

        rows.append(
            {
                "client_key": client_key,
                "name": nombre,
                "address": direccion,
                "phone1": tel1,
                "phone2": tel2,
            }
        )

    return upsert_clients(rows)
