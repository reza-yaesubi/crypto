"""Watchlist logic: list, add, and remove tracked pairs."""

import sqlite3
from uuid import uuid4

from app import config
from app.database import now_iso


class WatchlistError(Exception):
    """Raised on invalid watchlist operations (e.g. duplicate add)."""


def list_watchlist(conn: sqlite3.Connection, user_id: str = config.DEFAULT_USER_ID) -> list[dict]:
    rows = conn.execute(
        "SELECT pair FROM watchlist WHERE user_id = ? ORDER BY added_at", (user_id,)
    ).fetchall()
    return [{"pair": r["pair"]} for r in rows]


def add_watchlist(conn: sqlite3.Connection, pair: str, user_id: str = config.DEFAULT_USER_ID) -> dict:
    exists = conn.execute(
        "SELECT 1 FROM watchlist WHERE user_id = ? AND pair = ?", (user_id, pair)
    ).fetchone()
    if exists:
        raise WatchlistError("Pair already in watchlist")
    conn.execute(
        "INSERT INTO watchlist (id, user_id, pair, added_at) VALUES (?, ?, ?, ?)",
        (str(uuid4()), user_id, pair, now_iso()),
    )
    conn.commit()
    return {"pair": pair}


def remove_watchlist(conn: sqlite3.Connection, pair: str, user_id: str = config.DEFAULT_USER_ID) -> None:
    conn.execute(
        "DELETE FROM watchlist WHERE user_id = ? AND pair = ?", (user_id, pair)
    )
    conn.commit()
