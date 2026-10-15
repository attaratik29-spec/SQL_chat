"""
database.py - SQLite database initialization and schema introspection.
Pre-loads a realistic e-commerce sample database with Users, Categories,
Products, Orders, OrderItems, and Transactions tables.
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "ecommerce.db"))


# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL UNIQUE,
    description   TEXT,
    parent_id     INTEGER REFERENCES categories(category_id),
    created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    email         TEXT    NOT NULL UNIQUE,
    full_name     TEXT    NOT NULL,
    city          TEXT,
    country       TEXT    DEFAULT 'US',
    is_active     INTEGER DEFAULT 1,
    created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    sku           TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    description   TEXT,
    category_id   INTEGER NOT NULL REFERENCES categories(category_id),
    price         REAL    NOT NULL CHECK (price >= 0),
    stock_qty     INTEGER DEFAULT 0,
    is_active     INTEGER DEFAULT 1,
    created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(user_id),
    status        TEXT    NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending','processing','shipped','delivered','cancelled','refunded')),
    total_amount  REAL    NOT NULL DEFAULT 0,
    discount      REAL    DEFAULT 0,
    shipping_fee  REAL    DEFAULT 0,
    created_at    TEXT    DEFAULT (datetime('now')),
    shipped_at    TEXT,
    delivered_at  TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id),
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL    NOT NULL,
    subtotal      REAL    GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    user_id         INTEGER NOT NULL REFERENCES users(user_id),
    amount          REAL    NOT NULL,
    currency        TEXT    DEFAULT 'USD',
    payment_method  TEXT    CHECK (payment_method IN ('credit_card','debit_card','paypal','bank_transfer','crypto')),
    status          TEXT    DEFAULT 'completed'
                            CHECK (status IN ('pending','completed','failed','refunded')),
    created_at      TEXT    DEFAULT (datetime('now'))
);
"""

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

CATEGORIES = [
    (1, "Electronics",   "Gadgets and devices",        None),
    (2, "Clothing",      "Apparel and fashion",         None),
    (3, "Home & Garden", "Furniture and outdoor",       None),
    (4, "Sports",        "Fitness and outdoor gear",    None),
    (5, "Books",         "Physical and digital books",  None),
    (6, "Laptops",       "Portable computers",          1),
    (7, "Smartphones",   "Mobile phones",               1),
    (8, "Men's Wear",    "Men's clothing",              2),
    (9, "Women's Wear",  "Women's clothing",            2),
    (10, "Kitchen",      "Kitchen appliances",           3),
]

USERS = [
    ("alice_w",    "alice@example.com",   "Alice Williams",   "New York",    "US"),
    ("bob_smith",  "bob@example.com",     "Bob Smith",        "Los Angeles", "US"),
    ("carol_j",    "carol@example.com",   "Carol Johnson",    "Chicago",     "US"),
    ("david_b",    "david@example.com",   "David Brown",      "Houston",     "US"),
    ("emma_d",     "emma@example.com",    "Emma Davis",       "Phoenix",     "US"),
    ("frank_m",    "frank@example.com",   "Frank Miller",     "San Antonio", "US"),
    ("grace_w",    "grace@example.com",   "Grace Wilson",     "San Diego",   "US"),
    ("henry_t",    "henry@example.com",   "Henry Taylor",     "Dallas",      "US"),
    ("iris_a",     "iris@example.com",    "Iris Anderson",    "Austin",      "US"),
    ("jack_th",    "jack@example.com",    "Jack Thomas",      "Jacksonville","US"),
    ("karen_m",    "karen@example.com",   "Karen Martinez",   "Columbus",    "US"),
    ("leo_g",      "leo@example.com",     "Leo Garcia",       "San Jose",    "US"),
    ("mia_l",      "mia@example.com",     "Mia Lee",          "Seattle",     "US"),
    ("noah_h",     "noah@example.com",    "Noah Harris",      "Denver",      "US"),
    ("olivia_c",   "olivia@example.com",  "Olivia Clark",     "Nashville",   "US"),
    ("paul_l",     "paul@example.com",    "Paul Lewis",       "Portland",    "US"),
    ("quinn_r",    "quinn@example.com",   "Quinn Robinson",   "Las Vegas",   "US"),
    ("rachel_w",   "rachel@example.com",  "Rachel Walker",    "Louisville",  "US"),
    ("sam_ha",     "sam@example.com",     "Sam Hall",         "Baltimore",   "US"),
    ("tina_y",     "tina@example.com",    "Tina Young",       "Milwaukee",   "US"),
]

PRODUCTS = [
    ("SKU-001", "MacBook Pro 14\"",        "Apple M3 Pro laptop",            6,  1899.99, 45),
    ("SKU-002", "Dell XPS 15",             "Intel Core i9 laptop",           6,  1599.99, 32),
    ("SKU-003", "Lenovo ThinkPad X1",      "Business ultrabook",              6,  1299.99, 60),
    ("SKU-004", "iPhone 15 Pro",           "Apple flagship smartphone",       7,  1099.99, 120),
    ("SKU-005", "Samsung Galaxy S24",      "Android flagship",                7,   899.99, 150),
    ("SKU-006", "Google Pixel 8",          "Pure Android experience",         7,   699.99, 80),
    ("SKU-007", "Sony WH-1000XM5",         "Noise cancelling headphones",     1,   349.99, 200),
    ("SKU-008", "iPad Air 5",              "Apple tablet",                    1,   749.99, 90),
    ("SKU-009", "Men's Classic Tee",       "100% cotton t-shirt",             8,    29.99, 500),
    ("SKU-010", "Women's Yoga Pants",      "High-waist leggings",             9,    59.99, 350),
    ("SKU-011", "Running Shoes Men",       "Lightweight athletic shoes",      4,   119.99, 200),
    ("SKU-012", "Yoga Mat Premium",        "6mm thick non-slip mat",          4,    49.99, 300),
    ("SKU-013", "Python Crash Course",     "Programming book for beginners",  5,    39.99, 250),
    ("SKU-014", "The Clean Coder",         "Professional software guide",     5,    44.99, 180),
    ("SKU-015", "Instant Pot Pro",         "Multi-use pressure cooker",       10,  129.99, 100),
    ("SKU-016", "Air Fryer 5.8QT",        "Rapid air technology fryer",      10,   89.99, 140),
    ("SKU-017", "Samsung 4K TV 55\"",      "Crystal UHD display",             1,   799.99, 55),
    ("SKU-018", "Mechanical Keyboard",     "RGB backlit gaming keyboard",     1,   149.99, 175),
    ("SKU-019", "Women's Summer Dress",    "Floral print maxi dress",         9,    79.99, 220),
    ("SKU-020", "Men's Chino Pants",       "Slim-fit chinos",                 8,    69.99, 190),
]

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "bank_transfer", "crypto"]
ORDER_STATUSES = ["delivered", "delivered", "delivered", "shipped", "processing", "cancelled", "refunded"]


def _random_date(start_days_ago: int, end_days_ago: int = 0) -> str:
    delta = random.randint(end_days_ago, start_days_ago)
    dt = datetime.now() - timedelta(days=delta)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _seed_data(conn: sqlite3.Connection):
    cur = conn.cursor()

    # Categories
    cur.executemany(
        "INSERT OR IGNORE INTO categories (category_id, name, description, parent_id) VALUES (?,?,?,?)",
        CATEGORIES
    )

    # Users
    cur.executemany(
        "INSERT OR IGNORE INTO users (username, email, full_name, city, country) VALUES (?,?,?,?,?)",
        USERS
    )

    # Products
    cur.executemany(
        """INSERT OR IGNORE INTO products (sku, name, description, category_id, price, stock_qty)
           VALUES (?,?,?,?,?,?)""",
        PRODUCTS
    )

    conn.commit()

    # Check if orders already exist
    existing_orders = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if existing_orders > 0:
        return  # already seeded

    # Orders + OrderItems + Transactions (generate 80 realistic orders)
    user_ids   = [r[0] for r in cur.execute("SELECT user_id FROM users").fetchall()]
    product_rows = cur.execute("SELECT product_id, price FROM products").fetchall()

    for _ in range(80):
        uid        = random.choice(user_ids)
        status     = random.choice(ORDER_STATUSES)
        created_at = _random_date(365, 1)
        discount   = round(random.choice([0, 0, 0, 5, 10, 15, 20]), 2)
        shipping   = round(random.choice([0, 4.99, 7.99, 12.99]), 2)

        cur.execute(
            "INSERT INTO orders (user_id, status, total_amount, discount, shipping_fee, created_at) VALUES (?,?,?,?,?,?)",
            (uid, status, 0, discount, shipping, created_at)
        )
        order_id = cur.lastrowid

        # 1-4 items per order
        items        = random.sample(product_rows, k=random.randint(1, 4))
        total        = 0.0
        for prod_id, price in items:
            qty      = random.randint(1, 3)
            unit_p   = round(price * random.uniform(0.9, 1.05), 2)
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
                (order_id, prod_id, qty, unit_p)
            )
            total += qty * unit_p

        final_total = round(total - discount + shipping, 2)
        cur.execute("UPDATE orders SET total_amount=? WHERE order_id=?", (final_total, order_id))

        # Transaction
        txn_status = "completed" if status not in ("cancelled",) else "refunded"
        cur.execute(
            """INSERT INTO transactions (order_id, user_id, amount, currency, payment_method, status, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (order_id, uid, final_total, "USD",
             random.choice(PAYMENT_METHODS), txn_status, created_at)
        )

    conn.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create schema and seed sample data."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    _seed_data(conn)
    conn.close()
    print(f"[DB] Initialized at {DB_PATH}")


def get_schema() -> dict:
    """Return full schema metadata including columns and foreign keys."""
    conn = get_connection()
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
                    "name":       c["name"],
                    "type":       c["type"],
                    "not_null":   bool(c["notnull"]),
                    "pk":         bool(c["pk"]),
                    "default":    c["dflt_value"],
                }
                for c in cols
            ],
            "foreign_keys": [
                {
                    "from_col":   fk["from"],
                    "to_table":   fk["table"],
                    "to_col":     fk["to"],
                }
                for fk in fks
            ],
            "row_count": cur.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0],
        }

    conn.close()
    return schema
