# notion/contract_config.py

# Mapeo payload (Contrato||...) -> Notion properties (nombres exactos)
NOTION_CONTRACT_FIELDS = {
    "NContrato":          {"type": "title",        "path": "Contrato||Num_Cont"},
    "Nombre Cliente":     {"type": "rich_text",    "path": "Contrato||Cliente_Nom"},
    "Dirección":          {"type": "rich_text",    "path": "Contrato||Cliente_Dir"},
    "Teléfono 1":         {"type": "phone_number", "path": "Contrato||Cliente_Tel1"},
    "Teléfono 2":         {"type": "phone_number", "path": "Contrato||Cliente_Tel2"},
    "Fecha entrega":      {"type": "date",         "path": "Contrato||Entrega"},
    "Fecha venta":        {"type": "date",         "path": "Contrato||Fecha"},
    "Fecha prueba":       {"type": "date",         "path": "Contrato||Prueba"},
    "Valor del Contrato": {"type": "number",       "path": "Contrato||V_Total"},

    # Selects (deben existir en Notion con esas opciones)
    "Local":              {"type": "select",       "path": "Contrato||Local"},
    "Estatus":            {"type": "select",       "path": "Contrato||Estatus"},

    # Relations (requieren page_id(s), no texto)
    "Vestido":            {"type": "relation",     "path": "Contrato||Vestido_PageId"},
    "Vendedores":         {"type": "relation",     "path": "Contrato||Vendedores"},
}
