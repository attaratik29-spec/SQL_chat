"""
main.py - FastAPI application for the Text-to-SQL Engine.

Endpoints:
  GET  /api/schema           - Returns full database schema metadata
  POST /api/query            - Accepts NL query, returns clarification or result
  POST /api/query/clarified  - Accepts answered clarifications, returns SQL + data
  POST /api/upload-db        - Upload a SQLite .db or .sql file as active database
  GET  /api/active-db        - Returns the name of the currently active database
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import textwrap
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database as db_module
from database import init_db, get_schema
from nlp_engine import QueryAnalyser
from sql_generator import build_sql, execute_sql, validate_sql

# Holds the display name of the active database
_active_db_name: str = "E-Commerce SQLite"

# ---------------------------------------------------------------------------
# App initialisation & Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure SQLite database is created and seeded on application startup
    init_db()
    yield

app = FastAPI(
    title="Text-to-SQL Engine",
    description="Natural language to SQL with interactive clarification loop",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS safely for production (Render) and local development
cors_origins_env = os.environ.get("CORS_ORIGINS") or os.environ.get("FRONTEND_URL", "")
if cors_origins_env.strip() and cors_origins_env.strip() != "*":
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
    for dev_origin in ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]:
        if dev_origin not in allowed_origins:
            allowed_origins.append(dev_origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

analyser = QueryAnalyser()


# ---------------------------------------------------------------------------
# Health Check Endpoints (for Render, uptime monitors, and cloud deployments)
# ---------------------------------------------------------------------------

@app.get("/")
@app.get("/health")
@app.get("/api/health")
def health_check():
    """Returns 200 OK for Render health checks and connectivity verification."""
    return {
        "status": "healthy",
        "service": "Text-to-SQL Engine",
        "active_database": _active_db_name,
    }


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query:           str
    context_history: list[dict] = []


class ClarifiedQueryRequest(BaseModel):
    original_query:  str
    answers:         dict[str, str]          # { question_id: chosen_answer }
    partial_intent:  dict[str, Any] = {}


class DirectSQLRequest(BaseModel):
    sql: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/schema")
def schema_endpoint():
    """Return full database schema: tables, columns, types, FK relations, row counts."""
    return {
        "status": "success",
        "schema": get_schema(),
    }


@app.post("/api/query")
def query_endpoint(req: QueryRequest):
    """
    Accepts a natural language query.
    Returns either:
      { status: "clarification_needed", questions: [...], partial_intent: {...} }
    or:
      { status: "success", sql: "...", data: [...], columns: [...], row_count: N, execution_ms: N }
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = analyser.analyse(req.query, req.context_history)

    if result["status"] == "clarification_needed":
        return {
            "status":         "clarification_needed",
            "questions":      result["questions"],
            "partial_intent": result["partial_intent"],
            "original_query": result["original_query"],
            "message":        _build_clarification_message(result["ambiguities"]),
        }

    # Resolved — generate and execute SQL
    return _execute_intent(result["intent"])


@app.post("/api/query/clarified")
def clarified_query_endpoint(req: ClarifiedQueryRequest):
    """
    Merges clarification answers with the partial intent, generates final SQL, executes it.
    """
    if not req.original_query.strip():
        raise HTTPException(status_code=400, detail="Original query cannot be empty.")

    resolved = analyser.merge_clarifications(
        req.original_query,
        req.partial_intent,
        req.answers,
    )
    return _execute_intent(resolved["intent"])


@app.post("/api/query/direct-sql")
def direct_sql_endpoint(req: DirectSQLRequest):
    """
    Execute a raw SQL string (must be a safe SELECT statement).
    Useful for power users who want to run their own queries.
    """
    is_safe, err = validate_sql(req.sql)
    if not is_safe:
        raise HTTPException(status_code=400, detail=err)

    try:
        result = execute_sql(req.sql)
        return {
            "status":       "success",
            "sql":          req.sql.strip(),
            "data":         result["rows"],
            "columns":      result["columns"],
            "row_count":    result["row_count"],
            "execution_ms": result["execution_ms"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "text-to-sql-engine"}


@app.get("/api/active-db")
def active_db():
    """Return the name of the currently active database."""
    return {"name": _active_db_name}


@app.post("/api/upload-db")
async def upload_db(file: UploadFile = File(...)):
    """
    Upload a SQLite .db file or a plain .sql script.
    The file is validated and then set as the active database.
    """
    global _active_db_name

    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    if ext not in (".db", ".sqlite", ".sqlite3", ".sql"):
        raise HTTPException(
            status_code=400,
            detail="Only .db, .sqlite, .sqlite3, or .sql files are accepted.",
        )

    # Save to a temp file first for validation
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        if ext == ".sql":
            # Execute SQL script into a fresh SQLite DB
            new_db_path = tmp_path.replace(".sql", ".db")
            conn = sqlite3.connect(new_db_path)
            with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
                script = f.read()
            conn.executescript(script)
            conn.close()
            os.unlink(tmp_path)
            tmp_path = new_db_path
        else:
            # Validate it is a real SQLite file
            try:
                conn = sqlite3.connect(tmp_path)
                conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
                conn.close()
            except Exception:
                os.unlink(tmp_path)
                raise HTTPException(status_code=400, detail="File does not appear to be a valid SQLite database.")

        # Replace the active DB file
        dest = db_module.DB_PATH
        shutil.copy2(tmp_path, dest)
        os.unlink(tmp_path)

        _active_db_name = Path(filename).stem.replace("_", " ").replace("-", " ").title()
        return {
            "status": "success",
            "message": f"Database '{filename}' loaded successfully.",
            "db_name": _active_db_name,
            "schema": get_schema(),
        }
    except HTTPException:
        raise
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to process database: {str(e)}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _execute_intent(intent: dict) -> dict:
    try:
        sql    = build_sql(intent)
        result = execute_sql(sql)
        return {
            "status":       "success",
            "sql":          sql,
            "data":         result["rows"],
            "columns":      result["columns"],
            "row_count":    result["row_count"],
            "execution_ms": result["execution_ms"],
            "intent":       intent,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


def _build_clarification_message(ambiguities: list[str]) -> str:
    msgs = {
        "no_table":          "I couldn't identify which table you're referring to.",
        "ambiguous_metric":  "The metric you're asking about could mean several things.",
        "missing_limit":     "'Top' results need a number — how many would you like?",
        "missing_timeframe": "You mentioned a time-sensitive query — which period?",
    }
    parts = [msgs[a] for a in ambiguities if a in msgs]
    return " ".join(parts) or "Please clarify a few details before I generate the SQL."


# ---------------------------------------------------------------------------
# Production Server Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[Text-to-SQL Server] Running on http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)
