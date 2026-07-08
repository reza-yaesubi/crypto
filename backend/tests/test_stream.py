from app.main import create_app

# The live SSE flow (an infinite event-stream) is validated end-to-end with curl
# during increment validation; here we assert the route is wired up. The tick
# fan-out itself is covered deterministically in test_prices.py.


def test_stream_route_registered():
    app = create_app()
    assert "/api/stream/prices" in app.openapi()["paths"]
