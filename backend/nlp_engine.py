"""
nlp_engine.py - Rule-based Natural Language Processing engine.

Analyses a natural language query against the database schema and:
  1. Detects entities (tables, columns, metrics)
  2. Identifies ambiguities that require clarification
  3. Generates targeted clarification questions
  4. Merges clarification answers back into an intent dict
  5. Builds a structured "query intent" that sql_generator.py consumes
"""

from __future__ import annotations
import re
from typing import Any


# ---------------------------------------------------------------------------
# Keyword maps for table / metric / filter recognition
# ---------------------------------------------------------------------------

# Synonyms → canonical table name
TABLE_SYNONYMS: dict[str, str] = {
    "user": "users", "users": "users", "customer": "users", "customers": "users",
    "client": "users", "clients": "users", "account": "users", "accounts": "users",

    "product": "products", "products": "products", "item": "products", "items": "products",
    "goods": "products", "merchandise": "products", "inventory": "products",

    "category": "categories", "categories": "categories", "dept": "categories",
    "department": "categories", "type": "categories",

    "order": "orders", "orders": "orders", "purchase": "orders", "purchases": "orders",
    "sale": "orders", "sales": "orders", "transaction": "transactions",
    "transactions": "transactions", "payment": "transactions", "payments": "transactions",

    "order_item": "order_items", "order_items": "order_items",
    "line_item": "order_items", "line_items": "order_items",
}

# Synonyms → column / metric names
METRIC_SYNONYMS: dict[str, str] = {
    "revenue": "total_amount", "sales": "total_amount", "income": "total_amount",
    "earnings": "total_amount", "money": "total_amount", "value": "total_amount",
    "spend": "total_amount", "spending": "total_amount",

    "count": "COUNT(*)", "number": "COUNT(*)", "how many": "COUNT(*)",
    "total": "COUNT(*)",    # ambiguous – could be count or sum

    "price": "price", "cost": "price", "amount": "total_amount",
    "stock": "stock_qty", "quantity": "quantity", "qty": "quantity",
}

# Time-range keywords → SQL fragment
TIME_KEYWORDS: dict[str, str] = {
    "today":      "date(created_at) = date('now')",
    "yesterday":  "date(created_at) = date('now','-1 day')",
    "this week":  "created_at >= date('now','weekday 0','-7 days')",
    "last week":  "created_at BETWEEN date('now','weekday 0','-14 days') AND date('now','weekday 0','-7 days')",
    "this month": "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')",
    "last month": "strftime('%Y-%m', created_at) = strftime('%Y-%m', date('now','-1 month'))",
    "this year":  "strftime('%Y', created_at) = strftime('%Y', 'now')",
    "last year":  "strftime('%Y', created_at) = strftime('%Y', date('now','-1 year'))",
    "2023":       "strftime('%Y', created_at) = '2023'",
    "2024":       "strftime('%Y', created_at) = '2024'",
    "2025":       "strftime('%Y', created_at) = '2025'",
}

STATUS_KEYWORDS: list[str] = [
    "delivered", "shipped", "processing", "cancelled", "refunded", "pending"
]

SORT_KEYWORDS: dict[str, str] = {
    "top":     "DESC",
    "highest": "DESC",
    "most":    "DESC",
    "largest": "DESC",
    "lowest":  "ASC",
    "least":   "ASC",
    "bottom":  "ASC",
    "best":    "DESC",
    "worst":   "ASC",
}

AGG_KEYWORDS: dict[str, str] = {
    "total":    "SUM",
    "sum":      "SUM",
    "average":  "AVG",
    "avg":      "AVG",
    "mean":     "AVG",
    "minimum":  "MIN",
    "min":      "MIN",
    "maximum":  "MAX",
    "max":      "MAX",
    "count":    "COUNT",
    "number":   "COUNT",
    "how many": "COUNT",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _find_tables(text: str) -> list[str]:
    found = []
    for kw, table in TABLE_SYNONYMS.items():
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text):
            if table not in found:
                found.append(table)
    return found


def _find_metric(text: str) -> str | None:
    for kw, col in METRIC_SYNONYMS.items():
        if kw in text:
            return col
    return None


def _find_time(text: str) -> str | None:
    for kw, expr in TIME_KEYWORDS.items():
        if kw in text:
            return expr
    return None


def _find_limit(text: str) -> int | None:
    m = re.search(r"\b(\d+)\b", text)
    if m:
        return int(m.group(1))
    words = {"one": 1, "five": 5, "ten": 10, "twenty": 20, "fifty": 50, "hundred": 100}
    for w, n in words.items():
        if w in text:
            return n
    return None


def _find_sort(text: str) -> str | None:
    for kw, direction in SORT_KEYWORDS.items():
        if kw in text:
            return direction
    return None


def _find_agg(text: str) -> str | None:
    for kw, fn in AGG_KEYWORDS.items():
        if kw in text:
            return fn
    return None


def _find_status(text: str) -> list[str]:
    return [s for s in STATUS_KEYWORDS if s in text]


def _find_category_name(text: str) -> str | None:
    cats = [
        "electronics", "clothing", "home", "garden", "sports",
        "books", "laptops", "smartphones", "kitchen"
    ]
    for c in cats:
        if c in text:
            return c.title()
    return None


# ---------------------------------------------------------------------------
# Core Analyser
# ---------------------------------------------------------------------------

class QueryAnalyser:
    """Analyse a NL query and return either a resolved intent or clarification questions."""

    def analyse(self, query: str, context: list[dict]) -> dict[str, Any]:
        """
        Returns:
            {
              "status": "clarification_needed" | "resolved",
              "intent": {...},          # present if resolved
              "questions": [...],       # present if clarification_needed
              "original_query": str,
            }
        """
        text      = _normalise(query)
        tables    = _find_tables(text)
        metric    = _find_metric(text)
        time_expr = _find_time(text)
        limit     = _find_limit(text)
        sort_dir  = _find_sort(text)
        agg_fn    = _find_agg(text)
        statuses  = _find_status(text)
        cat_name  = _find_category_name(text)

        questions: list[dict] = []
        ambiguities: list[str] = []

        # ---- Ambiguity: no recognisable table ----
        if not tables:
            questions.append({
                "id":      "table",
                "text":    "Which data would you like to query?",
                "type":    "choice",
                "options": ["Orders / Sales", "Products / Inventory",
                            "Users / Customers", "Transactions / Payments",
                            "Order Items"],
            })
            ambiguities.append("no_table")

        # ---- Ambiguity: 'total' or 'sales' is ambiguous ----
        if "total" in text or "sales" in text:
            if agg_fn in (None, "COUNT", "SUM") and metric in (None, "COUNT(*)", "total_amount"):
                questions.append({
                    "id":      "metric",
                    "text":    "What do you mean by 'total' / 'sales'?",
                    "type":    "choice",
                    "options": [
                        "Total revenue (sum of order amounts)",
                        "Total number of orders (count)",
                        "Total number of items sold (quantity)",
                    ],
                })
                ambiguities.append("ambiguous_metric")

        # ---- Ambiguity: 'top' without a number ----
        if sort_dir == "DESC" and limit is None and "top" in text:
            questions.append({
                "id":      "limit",
                "text":    "How many top results would you like to see?",
                "type":    "choice",
                "options": ["Top 5", "Top 10", "Top 20", "Top 50"],
            })
            ambiguities.append("missing_limit")

        # ---- Ambiguity: no time range for time-sensitive queries ----
        time_sensitive_keywords = [
            "recent", "latest", "new", "trend", "growth", "monthly",
            "weekly", "annual", "yearly", "period",
        ]
        is_time_sensitive = any(k in text for k in time_sensitive_keywords)
        if time_expr is None and is_time_sensitive:
            questions.append({
                "id":      "timeframe",
                "text":    "Which time period are you interested in?",
                "type":    "choice",
                "options": [
                    "Today", "This week", "This month",
                    "Last month", "This year", "Last year",
                ],
            })
            ambiguities.append("missing_timeframe")

        # ---- If there are ambiguities, return clarification needed ----
        if questions:
            return {
                "status":         "clarification_needed",
                "questions":      questions,
                "ambiguities":    ambiguities,
                "partial_intent": {
                    "tables":    tables,
                    "metric":    metric,
                    "time_expr": time_expr,
                    "limit":     limit,
                    "sort_dir":  sort_dir,
                    "agg_fn":    agg_fn,
                    "statuses":  statuses,
                    "cat_name":  cat_name,
                },
                "original_query": query,
            }

        # ---- Fully resolved intent ----
        return {
            "status": "resolved",
            "intent": {
                "tables":    tables,
                "metric":    metric,
                "time_expr": time_expr,
                "limit":     limit or 50,
                "sort_dir":  sort_dir,
                "agg_fn":    agg_fn,
                "statuses":  statuses,
                "cat_name":  cat_name,
                "raw_query": query,
            },
            "original_query": query,
        }

    def merge_clarifications(
        self,
        original_query: str,
        partial_intent: dict,
        answers: dict[str, str],
    ) -> dict[str, Any]:
        """Merge clarification answers into the partial intent and resolve."""

        intent = dict(partial_intent)
        text   = _normalise(original_query)

        # ---- Table resolution ----
        if "table" in answers:
            mapping = {
                "Orders / Sales":          ["orders"],
                "Products / Inventory":    ["products"],
                "Users / Customers":       ["users"],
                "Transactions / Payments": ["transactions"],
                "Order Items":             ["order_items"],
            }
            intent["tables"] = mapping.get(answers["table"], intent.get("tables") or ["orders"])

        # ---- Metric resolution ----
        if "metric" in answers:
            ans = answers["metric"]
            if "revenue" in ans.lower():
                intent["metric"] = "total_amount"
                intent["agg_fn"] = "SUM"
            elif "number of orders" in ans.lower() or "count" in ans.lower():
                intent["metric"] = "COUNT(*)"
                intent["agg_fn"] = "COUNT"
            elif "quantity" in ans.lower() or "items sold" in ans.lower():
                intent["metric"] = "quantity"
                intent["agg_fn"] = "SUM"

        # ---- Limit resolution ----
        if "limit" in answers:
            m = re.search(r"\d+", answers["limit"])
            intent["limit"] = int(m.group()) if m else 10

        # ---- Timeframe resolution ----
        if "timeframe" in answers:
            mapping = {
                "Today":      TIME_KEYWORDS["today"],
                "This week":  TIME_KEYWORDS["this week"],
                "This month": TIME_KEYWORDS["this month"],
                "Last month": TIME_KEYWORDS["last month"],
                "This year":  TIME_KEYWORDS["this year"],
                "Last year":  TIME_KEYWORDS["last year"],
            }
            intent["time_expr"] = mapping.get(answers["timeframe"])

        # Ensure defaults
        intent.setdefault("limit",    50)
        intent.setdefault("sort_dir", None)
        intent.setdefault("agg_fn",   None)
        intent.setdefault("statuses", [])
        intent.setdefault("cat_name", None)
        intent["raw_query"] = original_query

        return {
            "status": "resolved",
            "intent": intent,
            "original_query": original_query,
        }
