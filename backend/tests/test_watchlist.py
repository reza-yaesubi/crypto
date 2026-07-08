import pytest

from app import config, database, watchlist


@pytest.fixture
def conn():
    database.init_db()
    connection = database.connect()
    yield connection
    connection.close()


def test_list_returns_seed(conn):
    assert len(watchlist.list_watchlist(conn)) == len(config.SEED_WATCHLIST)


def test_add_new_pair(conn):
    watchlist.add_watchlist(conn, "UNI-USD")
    pairs = {w["pair"] for w in watchlist.list_watchlist(conn)}
    assert "UNI-USD" in pairs


def test_add_duplicate_rejected(conn):
    with pytest.raises(watchlist.WatchlistError, match="already in watchlist"):
        watchlist.add_watchlist(conn, "BTC-USD")  # already seeded


def test_remove_pair(conn):
    watchlist.remove_watchlist(conn, "BTC-USD")
    pairs = {w["pair"] for w in watchlist.list_watchlist(conn)}
    assert "BTC-USD" not in pairs
