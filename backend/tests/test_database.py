from app import config, database


def _count(table: str) -> int:
    conn = database.connect()
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def test_init_creates_and_seeds():
    database.init_db()

    conn = database.connect()
    try:
        cash = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?",
            (config.DEFAULT_USER_ID,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert cash == config.STARTING_CASH
    assert _count("watchlist") == len(config.SEED_WATCHLIST)


def test_init_is_idempotent():
    database.init_db()
    database.init_db()

    assert _count("users_profile") == 1
    assert _count("watchlist") == len(config.SEED_WATCHLIST)
