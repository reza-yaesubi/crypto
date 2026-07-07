"""SQLite persistence: connection, lazy schema creation, and default seeding."""

import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users_profile (
    id TEXT PRIMARY KEY,
    cash_balance REAL NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    pair TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE (user_id, pair)
);
CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    pair TEXT NOT NULL,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (user_id, pair)
);
CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    pair TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    executed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    total_value REAL NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    actions TEXT,
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    """Current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    """Open a connection to the SQLite database, creating its directory if needed."""
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if missing and seed default data on an empty database."""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        _seed(conn)
        conn.commit()
    finally:
        conn.close()


def _seed(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM users_profile").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
            (config.DEFAULT_USER_ID, config.STARTING_CASH, now_iso()),
        )
    if conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO watchlist (id, user_id, pair, added_at) VALUES (?, ?, ?, ?)",
            [
                (str(uuid4()), config.DEFAULT_USER_ID, pair, now_iso())
                for pair in config.SEED_WATCHLIST
            ],
        )
