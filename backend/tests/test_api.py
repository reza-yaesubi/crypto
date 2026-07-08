from fastapi.testclient import TestClient

from app import config
from app.main import create_app


def test_portfolio_endpoint_shape():
    with TestClient(create_app()) as client:
        body = client.get("/api/portfolio").json()
    assert body["cash"] == config.STARTING_CASH
    assert body["total_value"] == config.STARTING_CASH
    assert body["positions"] == []


def test_watchlist_crud_endpoints():
    with TestClient(create_app()) as client:
        assert len(client.get("/api/watchlist").json()) == len(config.SEED_WATCHLIST)

        created = client.post("/api/watchlist", json={"pair": "UNI-USD"})
        assert created.status_code == 201
        assert created.json() == {"pair": "UNI-USD"}

        dup = client.post("/api/watchlist", json={"pair": "UNI-USD"})
        assert dup.status_code == 409

        removed = client.delete("/api/watchlist/UNI-USD")
        assert removed.status_code == 204
        pairs = {w["pair"] for w in client.get("/api/watchlist").json()}
        assert "UNI-USD" not in pairs


def test_trade_endpoint_updates_portfolio():
    with TestClient(create_app()) as client:
        # BTC-USD is a seeded simulator pair, so a market price exists.
        trade = client.post(
            "/api/portfolio/trade", json={"pair": "BTC-USD", "quantity": 0.1, "side": "buy"}
        ).json()
        assert trade["ok"] is True

        portfolio = client.get("/api/portfolio").json()
        assert portfolio["cash"] < config.STARTING_CASH
        assert portfolio["positions"][0]["pair"] == "BTC-USD"
        assert portfolio["positions"][0]["quantity"] == 0.1


def test_trade_rejects_insufficient_cash():
    with TestClient(create_app()) as client:
        resp = client.post(
            "/api/portfolio/trade", json={"pair": "BTC-USD", "quantity": 1000, "side": "buy"}
        )
        assert resp.status_code == 400
        assert resp.json() == {"ok": False, "error": "Insufficient cash"}
