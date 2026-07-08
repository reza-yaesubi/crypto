import pytest

from app import database, portfolio
from app.prices import PriceCache


@pytest.fixture
def conn():
    database.init_db()
    connection = database.connect()
    yield connection
    connection.close()


@pytest.fixture
def cache():
    c = PriceCache()
    c.update("BTC-USD", 100.0)
    return c


def test_buy_reduces_cash_and_creates_position(conn, cache):
    result = portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 10)
    assert result["ok"] is True
    assert result["cash_remaining"] == 10000.0 - 10 * 100.0

    p = portfolio.get_portfolio(conn, cache)
    assert p["cash"] == 9000.0
    assert p["positions"][0]["pair"] == "BTC-USD"
    assert p["positions"][0]["quantity"] == 10
    assert p["positions"][0]["avg_cost"] == 100.0


def test_second_buy_averages_cost(conn, cache):
    portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 10)  # @100
    cache.update("BTC-USD", 200.0)
    portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 10)  # @200

    pos = portfolio.get_portfolio(conn, cache)["positions"][0]
    assert pos["quantity"] == 20
    assert pos["avg_cost"] == 150.0  # (10*100 + 10*200) / 20


def test_sell_increases_cash_and_reduces_quantity(conn, cache):
    portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 10)
    portfolio.execute_trade(conn, cache, "BTC-USD", "sell", 4)

    p = portfolio.get_portfolio(conn, cache)
    assert p["cash"] == 10000.0 - 10 * 100.0 + 4 * 100.0
    assert p["positions"][0]["quantity"] == 6


def test_full_sell_removes_from_active_positions(conn, cache):
    portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 5)
    portfolio.execute_trade(conn, cache, "BTC-USD", "sell", 5)
    assert portfolio.get_portfolio(conn, cache)["positions"] == []


def test_insufficient_cash_rejected(conn, cache):
    with pytest.raises(portfolio.TradeError, match="Insufficient cash"):
        portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 1000)  # 100k > 10k


def test_insufficient_shares_rejected(conn, cache):
    with pytest.raises(portfolio.TradeError, match="Insufficient shares"):
        portfolio.execute_trade(conn, cache, "BTC-USD", "sell", 1)


def test_unknown_pair_rejected(conn, cache):
    with pytest.raises(portfolio.TradeError, match="No market price"):
        portfolio.execute_trade(conn, cache, "NOPE-USD", "buy", 1)


def test_unrealized_pnl(conn, cache):
    portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 10)  # @100
    cache.update("BTC-USD", 120.0)
    pos = portfolio.get_portfolio(conn, cache)["positions"][0]
    assert pos["unrealized_pnl"] == pytest.approx(200.0)  # (120-100)*10
    assert pos["pnl_pct"] == pytest.approx(20.0)


def test_trade_records_snapshot(conn, cache):
    portfolio.execute_trade(conn, cache, "BTC-USD", "buy", 1)
    assert len(portfolio.get_history(conn)) == 1
