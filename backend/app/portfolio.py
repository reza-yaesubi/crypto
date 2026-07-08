"""Paper-trading portfolio logic: valuation, trade execution, snapshots."""

import asyncio
import sqlite3
from uuid import uuid4

from app import config, database
from app.database import now_iso
from app.prices import PriceCache


class TradeError(Exception):
    """Raised when a trade fails validation (surfaced to the client as 400)."""


def get_portfolio(conn: sqlite3.Connection, cache: PriceCache, user_id: str = config.DEFAULT_USER_ID) -> dict:
    cash = conn.execute(
        "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
    ).fetchone()["cash_balance"]

    rows = conn.execute(
        "SELECT pair, quantity, avg_cost FROM positions WHERE user_id = ? AND quantity > 0",
        (user_id,),
    ).fetchall()

    positions = []
    holdings_value = 0.0
    for row in rows:
        tick = cache.get(row["pair"])
        current = tick.price if tick else row["avg_cost"]
        pnl = (current - row["avg_cost"]) * row["quantity"]
        pnl_pct = ((current / row["avg_cost"] - 1) * 100) if row["avg_cost"] else 0.0
        holdings_value += row["quantity"] * current
        positions.append(
            {
                "pair": row["pair"],
                "quantity": row["quantity"],
                "avg_cost": row["avg_cost"],
                "current_price": current,
                "unrealized_pnl": pnl,
                "pnl_pct": pnl_pct,
            }
        )

    return {"cash": cash, "total_value": cash + holdings_value, "positions": positions}


def execute_trade(
    conn: sqlite3.Connection,
    cache: PriceCache,
    pair: str,
    side: str,
    quantity: float,
    user_id: str = config.DEFAULT_USER_ID,
) -> dict:
    if quantity <= 0:
        raise TradeError("Quantity must be positive")
    if side not in ("buy", "sell"):
        raise TradeError("Side must be 'buy' or 'sell'")

    tick = cache.get(pair)
    if tick is None:
        raise TradeError(f"No market price for {pair}")
    price = tick.price

    cash = conn.execute(
        "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
    ).fetchone()["cash_balance"]
    pos = conn.execute(
        "SELECT * FROM positions WHERE user_id = ? AND pair = ?", (user_id, pair)
    ).fetchone()

    if side == "buy":
        cost = quantity * price
        if cost > cash:
            raise TradeError("Insufficient cash")
        new_cash = cash - cost
        if pos:
            new_qty = pos["quantity"] + quantity
            new_avg = (pos["quantity"] * pos["avg_cost"] + quantity * price) / new_qty
            conn.execute(
                "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? WHERE id = ?",
                (new_qty, new_avg, now_iso(), pos["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO positions (id, user_id, pair, quantity, avg_cost, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid4()), user_id, pair, quantity, price, now_iso()),
            )
    else:  # sell
        if pos is None or quantity > pos["quantity"]:
            raise TradeError("Insufficient shares")
        new_cash = cash + quantity * price
        conn.execute(
            "UPDATE positions SET quantity = ?, updated_at = ? WHERE id = ?",
            (pos["quantity"] - quantity, now_iso(), pos["id"]),
        )

    conn.execute(
        "UPDATE users_profile SET cash_balance = ? WHERE id = ?", (new_cash, user_id)
    )
    conn.execute(
        "INSERT INTO trades (id, user_id, pair, side, quantity, price, executed_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid4()), user_id, pair, side, quantity, price, now_iso()),
    )
    conn.commit()
    record_snapshot(conn, cache, user_id)

    return {
        "ok": True,
        "pair": pair,
        "side": side,
        "quantity": quantity,
        "price": price,
        "cash_remaining": new_cash,
    }


def record_snapshot(conn: sqlite3.Connection, cache: PriceCache, user_id: str = config.DEFAULT_USER_ID) -> None:
    total = get_portfolio(conn, cache, user_id)["total_value"]
    conn.execute(
        "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at)"
        " VALUES (?, ?, ?, ?)",
        (str(uuid4()), user_id, total, now_iso()),
    )
    conn.commit()


def get_history(conn: sqlite3.Connection, user_id: str = config.DEFAULT_USER_ID) -> list[dict]:
    rows = conn.execute(
        "SELECT recorded_at, total_value FROM portfolio_snapshots"
        " WHERE user_id = ? ORDER BY recorded_at",
        (user_id,),
    ).fetchall()
    return [{"recorded_at": r["recorded_at"], "total_value": r["total_value"]} for r in rows]


async def snapshot_loop(cache: PriceCache, stop: asyncio.Event, interval: float = 30.0) -> None:
    """Periodically record a portfolio-value snapshot for the P&L chart."""
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            conn = database.connect()
            try:
                record_snapshot(conn, cache)
            finally:
                conn.close()
