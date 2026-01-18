"""Funciones para aplicar mapeos de datos a documentos Word y Excel."""

from datetime import datetime
from win32com.client import constants  # type: ignore
import unicodedata

def get_value_from_path(data: dict, path: str):
    """
    Navega por un dict siguiendo una ruta tipo 'A||B||C'.

    - Usa '||' como separador de niveles, para que claves con puntos no se rompan.
    - Soporta concatenaciones con '+' y literales entre comillas simples.
    """
    if "+" in path:
        parts = [p.strip() for p in path.split("+")]
        values = []
        for part in parts:
            if part.startswith("'") and part.endswith("'"):
                values.append(part.strip("'"))
            else:
                values.append(str(get_value_from_path(data, part)))
        return "".join(values)
    keys = path.split("||")
    val = data
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            print(f"⚠️ Ruta no encontrada: {path} (faltó '{k}')")
            return ""
    return val

# Constantes mínimas para no depender de win32.constants
WD_FIND_CONTINUE = 1
WD_COLLAPSE_END = 0

def _replace_manual(rng, find_text, repl_text):
    """
    Busca find_text en el rango y lo reemplaza por repl_text (uno por uno).
    Devuelve cantidad de reemplazos.
    """
    f = rng.Find
    f.ClearFormatting()
    f.Text = find_text
    f.Forward = True
    f.Wrap = 1  # wdFindContinue
    count = 0
    while f.Execute():
        rng.Text = str(repl_text)
        count += 1
        rng.Collapse(0)  # wdCollapseEnd
        f = rng.Find
        f.Text = find_text
    return count

def apply_mappings(target, data: dict, config: dict):
    """
    Aplica el mapeo definido en config sobre el documento target (Word o Excel).
    """
    tipo = config["Tipo de documento"].lower()
    mappings = config["mapeo"]
    if tipo == "word":
        for placeholder, path in mappings.items():
            value = (
                get_value_from_path(data, path)
                if not str(path).startswith("__")
                else handle_special(path)
            )
            # Si value es lista, renderiza tabla y no hace replace normal
            if isinstance(value, list):
                inserted = _render_table_from_list(target, placeholder, value)
                print(f"→ {placeholder}: filas insertadas = {inserted}")
                continue
            total = 0
            # 1) Cuerpo principal
            rng = target.Content.Duplicate
            total += _replace_manual(rng, placeholder, value)
            # 2) Tablas (reemplazo escalar)
            try:
                for tbl in target.Tables:
                    for row in tbl.Rows:
                        for cell in row.Cells:
                            rng_cell = cell.Range.Duplicate
                            total += _replace_manual(rng_cell, placeholder, value)
            except Exception:
                pass
            print(f"→ {placeholder}: reemplazos hechos = {total}")
    elif tipo == "excel":
        for cell, path in mappings.items():
            value = (
                get_value_from_path(data, path)
                if not str(path).startswith("__")
                else handle_special(path)
            )
            rng = target.Range(cell)
            if path == "__TODAY__":
                rng.NumberFormat = "dd/mm/yyyy"
                rng.Value = value
            else:
                rng.NumberFormat = "@"
                rng.Value = str(value)
            print(f"Escrito {value} en {cell}")

def _render_table_from_list(doc, table_anchor_placeholder: str, rows_list: list) -> int:
    """
    Renderiza una tabla en Word a partir de una lista (rows_list).
    Busca una fila 'modelo' que contenga el placeholder anchor.

    Devuelve cuántas filas insertó.
    """
    if not rows_list:
        _remove_placeholder_everywhere(doc, table_anchor_placeholder)
        return 0
    try:
        for tbl in doc.Tables:
            for row in tbl.Rows:
                for cell in row.Cells:
                    cell_text = (cell.Range.Text or "")
                    if table_anchor_placeholder in cell_text:
                        template_row = row
                        inserted = 0
                        for item in reversed(rows_list):
                            new_row = tbl.Rows.Add(template_row)
                            try:
                                new_row.Range.FormattedText = template_row.Range.FormattedText
                            except Exception:
                                pass
                            _replace_manual(new_row.Range.Duplicate, table_anchor_placeholder, "")
                            _fill_row_from_item(new_row, item)
                            inserted += 1
                        try:
                            template_row.Delete()
                        except Exception:
                            _replace_manual(
                                template_row.Range.Duplicate, table_anchor_placeholder, ""
                            )
                        return inserted
    except Exception:
        pass
    return 0

def _fill_row_from_item(word_row, item):
    """
    item puede ser dict (recomendado) o valor simple.
    Si es dict: reemplaza [KEY] por VALUE dentro de la fila.
    """
    rng = word_row.Range.Duplicate
    if isinstance(item, dict):
        for k, v in item.items():
            ph = f"[{str(k).strip()}]"
            _replace_manual(rng, ph, "" if v is None else str(v))
    else:
        _replace_manual(rng, "[VALOR]", "" if item is None else str(item))

def _remove_placeholder_everywhere(doc, placeholder: str):
    """
    Limpia placeholder del documento completo (cuerpo + tablas).
    """
    try:
        _replace_manual(doc.Content.Duplicate, placeholder, "")
    except Exception:
        pass
    try:
        for tbl in doc.Tables:
            for row in tbl.Rows:
                for cell in row.Cells:
                    _replace_manual(cell.Range.Duplicate, placeholder, "")
    except Exception:
        pass

def handle_special(path: str):
    """Maneja valores especiales en el JSON de mapeos."""
    if path == "__TODAY__":
        return datetime.today()
    return None
