# notion/contracts.py
import json
from ms_bridal.integrations.notion.client import NotionClient, NotionError
from notion.keys import NOTION_DATABASE_ID
from ms_bridal.integrations.notion.contract_config import NOTION_CONTRACT_FIELDS

def get_value_from_path(data: dict, path: str):
    cur = data
    for part in path.split("||"):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur

def _as_rich_text(value) -> dict:
    s = "" if value is None else str(value)
    return {"rich_text": [{"text": {"content": s}}]}

def _as_title(value) -> dict:
    s = "" if value is None else str(value)
    return {"title": [{"text": {"content": s}}]}

def _as_number(value) -> dict:
    if value is None or str(value).strip() == "":
        return {"number": None}
    s = str(value).replace(".", "").replace(",", "").strip()
    try:
        return {"number": float(s)}
    except ValueError:
        raise NotionError(f"No pude convertir a número: {value}")

def _as_date(value) -> dict:
    # Notion espera "YYYY-MM-DD"
    if value is None or str(value).strip() == "":
        return {"date": None}
    return {"date": {"start": str(value).strip()}}

def _as_phone(value) -> dict:
    # Notion phone_number es string (puede incluir +57 si quieres)
    if value is None or str(value).strip() == "":
        return {"phone_number": None}
    return {"phone_number": str(value).strip()}

def _as_select(value) -> dict:
    if value is None or str(value).strip() == "":
        return {"select": None}
    return {"select": {"name": str(value).strip()}}

def _as_relation(value) -> dict:
    """
    Espera:
      - un string con page_id, o
      - una lista de page_id, o
      - lista de dicts ya formateados
    """
    if value is None or value == "":
        return {"relation": []}

    # si llega string => 1 relación
    if isinstance(value, str):
        v = value.strip()
        return {"relation": [{"id": v}]} if v else {"relation": []}

    # si llega lista
    if isinstance(value, list):
        rels = []
        for x in value:
            if isinstance(x, str) and x.strip():
                rels.append({"id": x.strip()})
            elif isinstance(x, dict) and "id" in x:
                rels.append({"id": x["id"]})
        return {"relation": rels}

    raise NotionError(f"Relación inválida (esperaba page_id o lista): {value}")

def build_properties_from_payload(payload: dict) -> dict:
    props = {}

    for notion_name, spec in NOTION_CONTRACT_FIELDS.items():
        ptype = spec["type"]
        path = spec["path"]
        value = get_value_from_path(payload, path)

        if ptype == "title":
            props[notion_name] = _as_title(value)
        elif ptype == "rich_text":
            props[notion_name] = _as_rich_text(value)
        elif ptype == "number":
            props[notion_name] = _as_number(value)
        elif ptype == "date":
            props[notion_name] = _as_date(value)
        elif ptype == "phone_number":
            props[notion_name] = _as_phone(value)
        elif ptype == "select":
            props[notion_name] = _as_select(value)
        elif ptype == "relation":
            props[notion_name] = _as_relation(value)
        else:
            raise NotionError(f"Tipo no soportado: {ptype}")
        
    print (props)

    return props

def create_contract_row(payload: dict) -> dict:
    client = NotionClient()
    props = build_properties_from_payload(payload)
    return client.create_page(NOTION_DATABASE_ID, props)
