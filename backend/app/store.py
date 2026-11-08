"""Tiny SQLite persistence (JSON columns). Good enough for a prototype; swap for Postgres later."""
from __future__ import annotations

import json
import secrets
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from .config import DB_PATH

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY, created TEXT, updated TEXT, lang TEXT, channel TEXT, partner_id TEXT,
    profile TEXT, messages TEXT, recommendation TEXT, stage TEXT, order_id TEXT, meta TEXT
);
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY, session_id TEXT, created TEXT, updated TEXT, lang TEXT,
    profile TEXT, items TEXT, contract_months INTEGER, quote TEXT, status TEXT,
    consent TEXT, kyc TEXT, timeline TEXT, assigned_to TEXT, contact TEXT, extras TEXT
);
CREATE TABLE IF NOT EXISTS documents (
    order_id TEXT, doc_type TEXT, uploaded TEXT, detected_type TEXT, quality TEXT, fields TEXT,
    PRIMARY KEY (order_id, doc_type)
);
CREATE TABLE IF NOT EXISTS wa_sessions (
    phone TEXT PRIMARY KEY, session_id TEXT, updated TEXT
);
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY, order_id TEXT, created TEXT, updated TEXT, category TEXT, text TEXT, status TEXT, detail TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, ref TEXT, type TEXT, detail TEXT
);
"""

JSON_COLS = {"meta", "profile", "messages", "recommendation", "items", "quote", "consent", "kyc", "timeline",
             "quality", "fields", "detail", "contact", "extras"}

# Columns added after the first release; ALTER them into older local databases.
MIGRATIONS = [("orders", "extras", "TEXT")]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(4).upper()}"


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(SCHEMA)
        for table, col, typ in MIGRATIONS:
            cols = {r[1] for r in _conn.execute(f"PRAGMA table_info({table})")}
            if col not in cols:
                _conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
        _conn.commit()
    return _conn


def reset(path: str | None = None):
    """Used by tests: point at a fresh database."""
    global _conn, DB_PATH
    if _conn is not None:
        _conn.close()
    _conn = None
    if path:
        DB_PATH = path


def _row(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in JSON_COLS & d.keys():
        if d[k] is not None:
            d[k] = json.loads(d[k])
    return d


def _dump(v):
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v


def insert(table: str, data: dict):
    cols = ", ".join(data)
    qs = ", ".join("?" for _ in data)
    with _lock:
        conn().execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({qs})", [_dump(v) for v in data.values()])
        conn().commit()


def update(table: str, key: dict, data: dict):
    sets = ", ".join(f"{k} = ?" for k in data)
    where = " AND ".join(f"{k} = ?" for k in key)
    with _lock:
        conn().execute(f"UPDATE {table} SET {sets} WHERE {where}", [_dump(v) for v in data.values()] + list(key.values()))
        conn().commit()


def get(table: str, **key) -> dict | None:
    where = " AND ".join(f"{k} = ?" for k in key)
    return _row(conn().execute(f"SELECT * FROM {table} WHERE {where}", list(key.values())).fetchone())


def select(table: str, where: str = "1=1", params: tuple = (), order: str = "") -> list[dict]:
    sql = f"SELECT * FROM {table} WHERE {where}" + (f" ORDER BY {order}" if order else "")
    return [_row(r) for r in conn().execute(sql, params).fetchall()]


def delete(table: str, **key):
    where = " AND ".join(f"{k} = ?" for k in key)
    with _lock:
        conn().execute(f"DELETE FROM {table} WHERE {where}", list(key.values()))
        conn().commit()


def log(ref: str, type_: str, detail: dict | None = None):
    """Audit log. Callers must pass already-masked values only."""
    insert("events", {"ts": now(), "ref": ref, "type": type_, "detail": detail or {}})
