# webui/builder/cache_db.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterable

# DB: webui/cache/catalogs.sqlite3
DB_PATH = Path(__file__).resolve().parents[1] / "cache" / "catalogs.sqlite3"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    con = _connect()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS dresses (
        page_id   TEXT PRIMARY KEY,
        name      TEXT,
        reference TEXT,
        status    TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_key TEXT PRIMARY KEY,
        name       TEXT,
        address    TEXT,
        phone1     TEXT,
        phone2     TEXT
    )
    """)

    con.commit()
    con.close()


# -------------------------
# DRESSES
# -------------------------
def upsert_dresses(rows: Iterable[Dict[str, Any]]) -> int:
    """
    rows: [{page_id, name, reference, status}, ...]
    """
    init_db()
    con = _connect()
    cur = con.cursor()

    n = 0
    for r in rows:
        page_id = (r.get("page_id") or "").strip()
        if not page_id:
            continue

        cur.execute("""
        INSERT INTO dresses(page_id, name, reference, status)
        VALUES(?,?,?,?)
        ON CONFLICT(page_id) DO UPDATE SET
            name=excluded.name,
            reference=excluded.reference,
            status=excluded.status
        """, (
            page_id,
            (r.get("name") or "").strip(),
            (r.get("reference") or "").strip(),
            (r.get("status") or "").strip(),
        ))
        n += 1

    con.commit()
    con.close()
    return n


def list_dresses(active_only: bool = True) -> List[Dict[str, Any]]:
    init_db()
    con = _connect()
    cur = con.cursor()

    if active_only:
        cur.execute("""
        SELECT page_id, name, reference, status
        FROM dresses
        WHERE (status IS NULL OR status = '' OR LOWER(status) IN ('activo','active','disponible','available'))
        ORDER BY name COLLATE NOCASE
        """)
    else:
        cur.execute("""
        SELECT page_id, name, reference, status
        FROM dresses
        ORDER BY name COLLATE NOCASE
        """)

    out = [dict(row) for row in cur.fetchall()]
    con.close()
    return out


def get_dress(page_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    con = _connect()
    cur = con.cursor()
    cur.execute = (page_id or "").strip()
    cur.execute("SELECT * FROM dresses WHERE page_id = ?", (R := (page_id or "").strip(),))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


# -------------------------
# CLIENTS
# -------------------------
def upsert_clients(rows: Iterable[Dict[str, Any]]) -> int:
    """
    rows: [{client_key, name, address, phone1, phone2}, ...]
    client_key: lo que tú definas como identificador (ej: cédula, o "NOMBRE|TEL")
    """
    init_db()
    con = _connect()
    cur = con.cursor()

    n = 0
    for r in rows:
        key = (r.get("client_key") or "").strip()
        if not key:
            continue

        cur.execute("""
        INSERT INTO clients(client_key, name, address, phone1, phone2)
        VALUES(?,?,?,?,?)
        ON CONFLICT(client_key) DO UPDATE SET
            name=excluded.name,
            address=excluded.address,
            phone1=excluded.phone1,
            phone2=excluded.phone2
        """, (
            key,
            (r.get("name") or "").strip(),
            (r.get("address") or "").strip(),
            (r.get("phone1") or "").strip(),
            (r.get("phone2") or "").strip(),
        ))
        n += 1

    con.commit()
    con.close()
    return n


def list_clients() -> List[Dict[str, Any]]:
    init_db()
    con = _connect()
    cur = con.cursor()
    cur.execute("""
    SELECT client_key, name, address, phone1, phone2
    FROM clients
    ORDER BY name COLLATE NOCASE
    """)
    out = [dict(row) for row in cur.fetchall()]
    con.close()
    return out


def get_client(client_key: str) -> Optional[Dict[str, Any]]:
    init_db()
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM clients WHERE client_key = ?", ((client_key or "").strip(),))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None
