"""
datasource.py - Multi-datasource manager.

Supports:
  • Built-in SQLite DB  (always available as "builtin")
  • Uploaded .db / .sqlite files  → opened directly
  • Uploaded .csv files           → loaded into in-memory SQLite via pandas
  • Uploaded .xlsx / .xls files   → each sheet becomes a table in in-memory SQLite

Thread-safety: connections are created per-request (not shared).
"""

from __future__ import annotations

import io
import os
import re
import sqlite3
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from database import DB_PATH

# ─────────────────────────────────────────────────────────────────────────────
# In-memory store of uploaded sources
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DataSource:
    id:        str
    name:      str
    kind:      str          # "builtin" | "sqlite" | "csv" | "excel"
    path:      str | None   # file path for sqlite; None for in-memory
    db_bytes:  bytes | None = field(default=None, repr=False)  # for csv/excel
    tables:    list[str]    = field(default_factory=list)
    created_at: float       = field(default_factory=time.time)


# Global registry  { source_id: DataSource }
_SOURCES: dict[str, DataSource] = {}

BUILTIN_ID = "builtin"


def _init_builtin():
    if BUILTIN_ID not in _SOURCES:
        _SOURCES[BUILTIN_ID] = DataSource(
            id=BUILTIN_ID,
            name="E-Commerce SQLite",
            kind="builtin",
            path=DB_PATH,
        )


_init_builtin()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_table_name(raw: str) -> str:
    """Sanitise a string so it's a valid SQLite identifier."""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", raw)
    if name and name[0].isdigit():
        name = "t_" + name
    return name.lower() or "table_0"


def _df_to_sqlite_bytes(frames: dict[str, pd.DataFrame]) -> bytes:
    """Write a dict of DataFrames into an in-memory SQLite and return its bytes."""
    buf = io.BytesIO()
    conn = sqlite3.connect(":memory:")
    for tname, df in frames.items():
        # Coerce object columns to strings so SQLite can store them
        df = df.where(pd.notnull(df), None)
        df.to_sql(tname, conn, if_exists="replace", index=False)
    # Serialise to bytes using sqlite3's backup API
    disk_conn = sqlite3.connect(buf_name := tempfile.mktemp(suffix=".db"))
    conn.backup(disk_conn)
    disk_conn.close()
    conn.close()
    with open(buf_name, "rb") as f:
        data = f.read()
    os.unlink(buf_name)
    return data


def _get_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def list_sources() -> list[dict]:
    _init_builtin()
    return [
        {
            "id":    s.id,
            "name":  s.name,
            "kind":  s.kind,
            "tables": s.tables,
            "created_at": s.created_at,
        }
        for s in _SOURCES.values()
    ]


def get_source(source_id: str) -> DataSource | None:
    return _SOURCES.get(source_id)


def get_connection_for(source_id: str) -> sqlite3.Connection:
    """Return an open sqlite3.Connection for the given source.  Caller must close it."""
    src = _SOURCES.get(source_id)
    if src is None:
        raise KeyError(f"Unknown data source: {source_id!r}")

    if src.kind in ("builtin", "sqlite"):
        conn = sqlite3.connect(src.path)
    else:
        # CSV / Excel: stored as bytes → open from temp file
        tmp = tempfile.mktemp(suffix=".db")
        with open(tmp, "wb") as f:
            f.write(src.db_bytes)
        conn = sqlite3.connect(tmp)
        # schedule cleanup — just leave the tempfile; OS will clean it eventually

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_schema_for(source_id: str) -> dict:
    """Same shape as database.get_schema() but for any registered source."""
    conn = get_connection_for(source_id)
    cur  = conn.cursor()
    tables = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()

    schema = {}
    for (tname,) in tables:
        cols = cur.execute(f"PRAGMA table_info({tname})").fetchall()
        fks  = cur.execute(f"PRAGMA foreign_key_list({tname})").fetchall()
        schema[tname] = {
            "columns": [
                {
                    "name":     c[1],
                    "type":     c[2],
                    "not_null": bool(c[3]),
                    "pk":       bool(c[5]),
                    "default":  c[4],
                }
                for c in cols
            ],
            "foreign_keys": [
                {"from_col": fk[3], "to_table": fk[2], "to_col": fk[4]}
                for fk in fks
            ],
            "row_count": cur.execute(f"SELECT COUNT(*) FROM \"{tname}\"").fetchone()[0],
        }
    conn.close()
    return schema


def register_sqlite(file_bytes: bytes, filename: str) -> DataSource:
    tmp = tempfile.mktemp(suffix=".db")
    with open(tmp, "wb") as f:
        f.write(file_bytes)

    conn = sqlite3.connect(tmp)
    tables = _get_tables(conn)
    conn.close()

    src = DataSource(
        id=str(uuid.uuid4()),
        name=filename,
        kind="sqlite",
        path=tmp,
        tables=tables,
    )
    _SOURCES[src.id] = src
    return src


def register_csv(file_bytes: bytes, filename: str) -> DataSource:
    tname = _safe_table_name(os.path.splitext(filename)[0])
    df = pd.read_csv(io.BytesIO(file_bytes))
    db_bytes = _df_to_sqlite_bytes({tname: df})

    src = DataSource(
        id=str(uuid.uuid4()),
        name=filename,
        kind="csv",
        path=None,
        db_bytes=db_bytes,
        tables=[tname],
    )
    _SOURCES[src.id] = src
    return src


def register_excel(file_bytes: bytes, filename: str) -> DataSource:
    xl = pd.ExcelFile(io.BytesIO(file_bytes))
    frames = {}
    for sheet in xl.sheet_names:
        tname = _safe_table_name(sheet)
        frames[tname] = xl.parse(sheet)

    db_bytes = _df_to_sqlite_bytes(frames)

    src = DataSource(
        id=str(uuid.uuid4()),
        name=filename,
        kind="excel",
        path=None,
        db_bytes=db_bytes,
        tables=list(frames.keys()),
    )
    _SOURCES[src.id] = src
    return src


def delete_source(source_id: str) -> bool:
    if source_id == BUILTIN_ID:
        return False  # can't delete built-in
    src = _SOURCES.pop(source_id, None)
    if src and src.path and src.kind == "sqlite":
        try:
            os.unlink(src.path)
        except OSError:
            pass
    return src is not None
