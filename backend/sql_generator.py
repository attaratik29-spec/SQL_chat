"""
sql_generator.py - Safe SQL generation and execution.

Takes a resolved query intent (from nlp_engine.py) and:
  1. Builds a valid SQLite SELECT statement
  2. Validates the SQL for safety (whitelist-only)
  3. Executes it against the database
  4. Returns rows + metadata
"""

from __future__ import annotations
import re
import sqlite3
import time
from typing import Any

from database import get_connection

# ---------------------------------------------------------------------------
# Safety Validator
# ---------------------------------------------------------------------------

_DANGEROUS_PATTERN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH|PRAGMA)\b",
    re.IGNORECASE,
)
_ALLOWED_START = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_MULTI_STMT    = re.compile(r";.*\S", re.DOTALL)  # multiple statements


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Returns (is_safe, error_message).
    Only allows single SELECT statements with no dangerous keywords.
    """
    stripped = sql.strip()

    if not _ALLOWED_START.match(stripped):
        return False, "Only SELECT statements are permitted."

    if _DANGEROUS_PATTERN.search(stripped):
        return False, "Query contains forbidden keywords (DROP/DELETE/UPDATE etc.)."

    if _MULTI_STMT.search(stripped):
        return False, "Multiple statements are not allowed."

    # Block comment-based injection tricks
    if "--" in stripped or "/*" in stripped:
        return False, "SQL comments are not allowed."

    return True, ""


# ---------------------------------------------------------------------------
# SQL Builder
# ---------------------------------------------------------------------------

def _primary_table(intent: dict) -> str:
    tables = intent.get("tables") or ["orders"]
    return tables[0]


def _build_select_clause(intent: dict, primary: str) -> str:
    agg    = intent.get("agg_fn")
    metric = intent.get("metric")
    sort   = intent.get("sort_dir")

    # ---- Aggregation queries ----
    if agg and agg != "COUNT" and metric and metric != "COUNT(*)":
        if primary == "orders":
            return f"""
SELECT
    u.full_name          AS customer,
    COUNT(o.order_id)    AS order_count,
    {agg}(o.{metric})   AS aggregated_value
FROM orders o
JOIN users u ON u.user_id = o.user_id
""".strip()

        elif primary == "products":
            return f"""
SELECT
    p.name               AS product,
    c.name               AS category,
    {agg}(oi.{metric})  AS aggregated_value
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
JOIN categories c ON c.category_id = p.category_id
""".strip()

        elif primary == "transactions":
            return f"""
SELECT
    t.payment_method,
    COUNT(t.transaction_id) AS transaction_count,
    {agg}(t.amount)         AS aggregated_value
FROM transactions t
""".strip()

    # ---- COUNT queries ----
    if agg == "COUNT" or (metric == "COUNT(*)"):
        if primary == "orders":
            return """
SELECT
    u.full_name          AS customer,
    COUNT(o.order_id)    AS order_count
FROM orders o
JOIN users u ON u.user_id = o.user_id
""".strip()
        elif primary == "products":
            return """
SELECT
    c.name               AS category,
    COUNT(p.product_id)  AS product_count
FROM products p
JOIN categories c ON c.category_id = p.category_id
""".strip()
        elif primary == "users":
            return "SELECT user_id, username, full_name, city, country, created_at FROM users"
        elif primary == "transactions":
            return """
SELECT
    payment_method,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM transactions
""".strip()

    # ---- Default SELECT for each table ----
    defaults: dict[str, str] = {
        "orders": """
SELECT
    o.order_id,
    u.full_name      AS customer,
    o.status,
    o.total_amount,
    o.discount,
    o.shipping_fee,
    o.created_at
FROM orders o
JOIN users u ON u.user_id = o.user_id
""".strip(),
        "users": "SELECT user_id, username, full_name, city, country, is_active, created_at FROM users",
        "products": """
SELECT
    p.product_id,
    p.sku,
    p.name,
    c.name   AS category,
    p.price,
    p.stock_qty,
    p.is_active
FROM products p
JOIN categories c ON c.category_id = p.category_id
""".strip(),
        "categories": "SELECT category_id, name, description, parent_id, created_at FROM categories",
        "order_items": """
SELECT
    oi.item_id,
    o.order_id,
    p.name    AS product,
    oi.quantity,
    oi.unit_price,
    oi.subtotal
FROM order_items oi
JOIN orders   o ON o.order_id   = oi.order_id
JOIN products p ON p.product_id = oi.product_id
""".strip(),
        "transactions": """
SELECT
    t.transaction_id,
    u.full_name       AS customer,
    t.amount,
    t.currency,
    t.payment_method,
    t.status,
    t.created_at
FROM transactions t
JOIN users u ON u.user_id = t.user_id
""".strip(),
    }
    return defaults.get(primary, f"SELECT * FROM {primary}")


def _build_where_clauses(intent: dict) -> list[str]:
    clauses = []

    if intent.get("time_expr"):
        clauses.append(intent["time_expr"])

    if intent.get("statuses"):
        quoted   = ", ".join(f"'{s}'" for s in intent["statuses"])
        clauses.append(f"status IN ({quoted})")

    if intent.get("cat_name"):
        clauses.append(f"c.name = '{intent['cat_name']}'")

    return clauses


def _build_group_by(intent: dict, primary: str) -> str:
    agg = intent.get("agg_fn")
    if not agg:
        return ""
    if primary == "orders":
        return "GROUP BY o.user_id"
    elif primary == "products":
        return "GROUP BY oi.product_id" if agg != "COUNT" else "GROUP BY p.category_id"
    elif primary == "transactions":
        return "GROUP BY t.payment_method"
    return ""


def _build_order_by(intent: dict, primary: str) -> str:
    sort = intent.get("sort_dir")
    agg  = intent.get("agg_fn")

    if sort:
        if agg:
            return f"ORDER BY aggregated_value {sort}"
        if primary in ("orders", "transactions"):
            return f"ORDER BY created_at {sort}"
        return f"ORDER BY 1 {sort}"

    # Default ordering
    if primary in ("orders", "transactions"):
        return "ORDER BY created_at DESC"
    if primary == "products":
        return "ORDER BY p.price DESC"
    return ""


def build_sql(intent: dict) -> str:
    """Assemble a SQL SELECT from a resolved intent dict."""
    primary = _primary_table(intent)
    select  = _build_select_clause(intent, primary)
    wheres  = _build_where_clauses(intent)
    groupby = _build_group_by(intent, primary)
    orderby = _build_order_by(intent, primary)
    limit   = intent.get("limit") or 50

    sql = select
    if wheres:
        # Insert WHERE before GROUP BY / ORDER BY if present in select
        where_str = " AND ".join(wheres)
        if "WHERE" in sql.upper():
            sql += f"\n  AND {where_str}"
        else:
            sql += f"\nWHERE {where_str}"

    if groupby:
        sql += f"\n{groupby}"
    if orderby:
        sql += f"\n{orderby}"

    sql += f"\nLIMIT {limit}"

    return sql.strip()


# ---------------------------------------------------------------------------
# SQL Executor
# ---------------------------------------------------------------------------

def execute_sql(sql: str) -> dict[str, Any]:
    """
    Validate and execute a SQL string.
    Returns:
        { "rows": [...], "columns": [...], "row_count": int, "execution_ms": float }
    """
    is_safe, err = validate_sql(sql)
    if not is_safe:
        raise ValueError(f"SQL safety check failed: {err}")

    conn = get_connection()
    try:
        t0  = time.perf_counter()
        cur = conn.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
        columns    = [d[0] for d in cur.description] if cur.description else []
        return {
            "rows":         rows,
            "columns":      columns,
            "row_count":    len(rows),
            "execution_ms": elapsed_ms,
        }
    finally:
        conn.close()
