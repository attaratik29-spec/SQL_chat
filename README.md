# SQL Whisperer — Text-to-SQL Engine with Interactive Clarification Loop

A production-ready full-stack application that translates **natural language** into safe, executable **SQL queries** with an intelligent clarification loop for ambiguous queries.

---

## 🗂 Project Structure

```
SQL_chat/
├── backend/
│   ├── requirements.txt      # Python dependencies
│   ├── database.py           # SQLite schema + sample data seeder
│   ├── nlp_engine.py         # Rule-based NLP + ambiguity detection
│   ├── sql_generator.py      # SQL builder + safety validator + executor
│   ├── main.py               # FastAPI app + all endpoints
│   └── ecommerce.db          # Auto-generated on first startup
└── frontend/
    ├── package.json
    ├── vite.config.js         # Vite + /api proxy to :8000
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx            # Root dashboard layout + state
        ├── index.css          # Global styles + dark theme
        ├── api/
        │   └── client.js      # Axios API wrapper
        └── components/
            ├── SchemaViewer.jsx       # Sidebar schema explorer
            ├── QueryInput.jsx         # NL query input + examples
            ├── ClarificationWidget.jsx # Interactive clarification UI
            ├── SqlBlock.jsx            # Syntax-highlighted SQL display
            └── ResultsPanel.jsx       # Paginated data table
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** (LTS)

---

### 1. Start the Backend

```bash
cd SQL_chat/backend

# Install dependencies (one-time)
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will:
- Auto-create `ecommerce.db` with 6 tables and 80+ sample records
- Expose the API at `http://localhost:8000`
- Show interactive docs at `http://localhost:8000/docs`

---

### 2. Start the Frontend

```bash
cd SQL_chat/frontend

# Install dependencies (one-time)
npm install

# Start Vite dev server
npm run dev
```

Open **http://localhost:5173** in your browser.

The Vite proxy automatically forwards `/api/*` requests to the backend.

---

## 🔌 API Reference

### `GET /api/schema`
Returns full database schema (tables, columns, types, FK relations, row counts).

### `POST /api/query`
```json
{
  "query": "Show me top customers",
  "context_history": []
}
```
**Response (ambiguous):**
```json
{
  "status": "clarification_needed",
  "questions": [
    { "id": "metric", "text": "What do you mean by top?", "type": "choice", "options": [...] }
  ],
  "partial_intent": { ... },
  "original_query": "Show me top customers"
}
```
**Response (resolved):**
```json
{
  "status": "success",
  "sql": "SELECT ...",
  "data": [ {...}, ... ],
  "columns": ["customer", "order_count"],
  "row_count": 10,
  "execution_ms": 2.4
}
```

### `POST /api/query/clarified`
```json
{
  "original_query": "Show me top customers",
  "answers": { "metric": "Total revenue (sum of order amounts)", "limit": "Top 10" },
  "partial_intent": { ... }
}
```
Returns same `success` response as above.

### `POST /api/query/direct-sql`
```json
{ "sql": "SELECT * FROM users LIMIT 5" }
```
Executes a raw SELECT (safety validated) and returns rows.

---

## 🛡 Security Features

- **Whitelist-only**: Only `SELECT` statements are ever executed
- **Keyword blocking**: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE` etc. are rejected
- **Multi-statement blocking**: Semicolon-injected second statements are detected
- **Comment blocking**: `--` and `/*` patterns are rejected

---

## 🗃 Sample Database Schema

| Table | Description | Rows |
|---|---|---|
| `users` | Customers with name, email, city | 20 |
| `categories` | Product categories with parent | 10 |
| `products` | SKU, name, price, stock | 20 |
| `orders` | Orders with status, total, discount | 80 |
| `order_items` | Line items linking orders ↔ products | ~160 |
| `transactions` | Payment records per order | 80 |

---

## 💡 Example Queries to Try

| Natural Language | What Happens |
|---|---|
| `Show top 10 customers by revenue` | Resolved directly → SQL + table |
| `Show me top sales` | Clarification: metric? limit? |
| `List recent orders` | Clarification: which time period? |
| `Products in Electronics` | Resolved → filtered product list |
| `Show cancelled orders` | Resolved → filtered order list |
| `Total revenue by payment method` | Resolved → aggregated table |
| `Show me recent trends` | Clarification: data + timeframe |
